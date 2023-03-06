import os                                        #*************************************************************
import contextlib                                #
import argparse                                  #
import torchvision                               #
import torchvision.transforms as transforms      #
import torchvision.models as models              #             
from torch.utils.checkpoint import checkpoint_sequential         
import torch                                     #
import numpy as np                               #   ###       DON'T MODIFY    ####################
import apex                                      #
import wandb                                     #
                                                 #
import idr_torch                                 #
from dlojz_chrono import Chronometer             #
                                                 #
import random                                    #
random.seed(123)                                 #
np.random.seed(123)                              #
torch.manual_seed(123)                           #*************************************************************

## import ... ## Add here the libraries to import


def main():                                                                       #******************************************
    parser = argparse.ArgumentParser()                                            #
    parser.add_argument('-b', '--batch-size', default=128, type =int,             #
                        help='batch size per GPU')                                #
    parser.add_argument('-e','--epochs', default=1, type=int,                     #
                        help='number of total epochs to run')                     #
    parser.add_argument('--image-size', default=224, type=int,                    #
                        help='Image size')                                        #
    parser.add_argument('--lr', default=0.1, type=float,                          #
                        help='learning rate')                                     #
    parser.add_argument('--wd', default=0., type=float,                           #
                        help='weight decay')                                      #
    parser.add_argument('--mom', default=0.9, type=float,                         #
                        help='momentum')                                          #
    parser.add_argument('--test', default=False, action='store_true',             #      ##    DON'T MODIFY    ######## 
                        help='Test 50 iterations')                                #
    parser.add_argument('--test-nsteps', default='50', type=int,                  #
                        help='the number of steps in test mode')                  #
    parser.add_argument('--findlr', default=False, action='store_true',           #
                        help='LR finder')                                         # 
    parser.add_argument('--num-workers', default=10, type=int,                    #
                        help='num workers in dataloader')                         #
    parser.add_argument('--persistent-workers', default=True, action=argparse.BooleanOptionalAction,# 
                        help='activate persistent workers in dataloader')         #
    parser.add_argument('--pin-memory', default=True, action=argparse.BooleanOptionalAction,        #
                        help='activate pin memory option in dataloader')          #
    parser.add_argument('--non-blocking', default=True, action=argparse.BooleanOptionalAction,      #
                        help='activate asynchronuous GPU transfer')               #
    parser.add_argument('--prefetch-factor', default=3, type=int,                 #
                        help='prefectch factor in dataloader')                    #
    parser.add_argument('--drop-last', default=False, action=argparse.BooleanOptionalAction,        #
                        help='activate drop_last option in dataloader')           #******************************************
    
      
    args = parser.parse_args()

    train(args)
    

VAL_BATCH_SIZE=256


def train(args):
    
    ## chronometer initialisation (test and rank)
    chrono = Chronometer(args.test, idr_torch.rank)       ### DON'T MODIFY ### 
    
    # configure distribution method: define rank and initialise communication backend (NCCL)
    # TODO
    
    # define model
    
    model = models.resnet50()
    
    archi_model = 'Resnet-50'
    if idr_torch.rank == 0: print(f'model: {archi_model}')  ### DON'T MODIFY ###
    if idr_torch.rank == 0: print('number of parameters: {}'.format(sum([p.numel() ### DON'T MODIFY ###
                                              for p in model.parameters()]))) ### DON'T MODIFY ###
    
    
    # distribute batch size (mini-batch)                             #*************************************************
    num_replica = idr_torch.size                                     #
    mini_batch_size = args.batch_size                                #
    global_batch_size = mini_batch_size * num_replica                #
                                                                     #          ### DON'T MODIFY ################## 
    if idr_torch.rank == 0:                                          #
        print(f'global batch size: {global_batch_size} - mini batch size: {mini_batch_size}')
                                                                     #*************************************************
    
    # define loss function (criterion) and optimizer
    criterion = torch.nn.CrossEntropyLoss(label_smoothing=0.1) 
    optimizer = torch.optim.SGD(model.parameters(), args.lr, momentum=args.mom, weight_decay=args.wd)
    
    if idr_torch.rank == 0: print(f'Optimizer: {optimizer}')    ### DON'T MODIFY ###
        

    #########  DATALOADER ############ 
    # Define a transform to pre-process the training images.

    if idr_torch.rank == 0: print(f"DATALOADER {args.num_workers} {args.persistent_workers} {args.pin_memory} {args.non_blocking} {args.prefetch_factor} {args.drop_last} ") ### DON'T MODIFY ###

    transform = transforms.Compose([ 
            transforms.RandomResizedCrop(args.image_size),  # Random resize - Data Augmentation
            transforms.RandomHorizontalFlip(),              # Horizontal Flip - Data Augmentation
            transforms.ToTensor(),                          # convert the PIL Image to a tensor
            transforms.Normalize(mean=(0.485, 0.456, 0.406),
                                 std=(0.229, 0.224, 0.225))
            ])
        
    
    
    train_dataset = torchvision.datasets.ImageNet(root=os.environ['ALL_CCFRSCRATCH']+'/imagenet',
                                                  transform=transform)
    
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                               batch_size=mini_batch_size,
                                               shuffle=True,
                                               num_workers=args.num_workers,
                                               persistent_workers=args.persistent_workers,
                                               pin_memory=args.pin_memory,
                                               prefetch_factor=args.prefetch_factor,
                                               drop_last=args.drop_last)
    
        
    val_transform = transforms.Compose([
              transforms.Resize((256, 256)),
              transforms.CenterCrop(224),
              transforms.ToTensor(),   # convert the PIL Image to a tensor
              transforms.Normalize(mean=(0.485, 0.456, 0.406),
                                   std=(0.229, 0.224, 0.225))])
    
    val_dataset = torchvision.datasets.ImageNet(root=os.environ['ALL_CCFRSCRATCH']+'/imagenet', split='val',
                        transform=val_transform)
    
    val_loader = torch.utils.data.DataLoader(dataset=val_dataset,    
                                             batch_size=VAL_BATCH_SIZE,
                                             shuffle=False,
                                             num_workers=args.num_workers,
                                             persistent_workers=args.persistent_workers,
                                             pin_memory=args.pin_memory,
                                             prefetch_factor=args.prefetch_factor,
                                             drop_last=args.drop_last)
    
    N_batch = len(train_loader)
    N_val_batch = len(val_loader)
    N_val = len(val_dataset)
    
        
    ## LR Finder #####                                             #***************************************************
    if args.findlr:                                                #
        if args.lr == 0.1: args.lr = 10                            #
        lrs, losses=[],[]                                          #
        mult = (args.lr / 1e-8) ** (1/((N_batch*args.epochs)-1))   #       ### DON'T MODIFY #########################
        optimizer.param_groups[0]['lr'] = 1e-8                     #
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=mult) 
                                                                   #
    else:                                                          #***************************************************
        #LR scheduler to accelerate the training time
        scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=args.lr,
                                                    steps_per_epoch=N_batch, epochs=args.epochs)

    
    
    chrono.start()     ### DON'T MODIFY ####                                    
    
    ## Initialisation 
    if idr_torch.rank == 0: accuracies = []
    val_loss = torch.Tensor([0.])                  #TODO : send to GPU
    val_accuracy = torch.Tensor([0.])              #TODO : send to GPU
    
    ### Weight and biases initialization                                   #**********************************************
    if not args.test and idr_torch.rank == 0:                              #
        config = dict(                                                     #
          architecture = archi_model,                                      #
          batch_size = args.batch_size,                                    #
          epochs = args.epochs,                                            #
          image_size = args.image_size,                                    #
          learning_rate = args.lr,                                         #
          weight_decay = args.wd,                                          #
          momentum = args.mom,                                             #
          optimizer = optimizer.__class__.__name__,                        #
          lr_scheduler = scheduler.__class__.__name__                      #     ### DON'T MODIFY ##################
        )                                                                  #
                                                                           #
        wandb.init(                                                        #
          project="Imagenet Race Cup",                                     #
          entity="dlojz",                                                  #
          name=os.environ['SLURM_JOB_NAME']+'_'+os.environ['SLURM_JOBID'], #
          tags=['label smoothing'],                                        #
          config=config,                                                   #
          mode='offline'                                                   #
          )                                                                #
        wandb.watch(model, log="all", log_freq=N_batch)                    #********************************************
    
    #### TRAINING ############
    for epoch in range(args.epochs):    
        
        chrono.dataload()                                    #**********************************************************
        if idr_torch.rank == 0: chrono.tac_time(clear=True)  #
                                                             #
        for i, (images, labels) in enumerate(train_loader):  #        
                                                             #       ### DON'T MODIFY ##########################
            csteps = i + 1 + epoch * N_batch                 #
            if args.test and csteps > args.test_nsteps: break              #
            if i == 0 and idr_torch.rank == 0:               #
                print(f'image batch shape : {images.size()}')#
                                                             #**********************************************************
            
            # distribution of images and labels to all GPUs
            # TODO
            
            chrono.dataload()   #*******************************************************************************
            chrono.training()   #            ### DON'T MODIFY ##################
            chrono.forward()    #*******************************************************************************

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)

            chrono.forward()    #*******************************************************************************
            chrono.backward()   #             ### DON'T MODIFY ################
                                #*******************************************************************************            

            loss.backward()
            optimizer.step()

            # Metric mesurement
            _, predicted = torch.max(outputs.data, 1)      
            accuracy = (predicted == labels).sum() / labels.size(0)
            if idr_torch.rank == 0: accuracies.append(accuracy.item())
                
                                                            #*****************************************************
            if not args.test and idr_torch.rank == 0 and csteps%10 == 0:                                         
                wandb.log({"train accuracy": accuracy.item(),
                           "train loss":  loss.item(),      #
                           "learning rate": scheduler.get_lr()[0]}, step=csteps)
                                                            #
            chrono.backward()                               #
            chrono.training()                               #        ### DON'T MODIFY ############
                                                            #
            if args.findlr:                                 #
                lrs.append(scheduler.get_lr()[0])           #
                losses.append(loss.item())                  #     
                                                            #
            elif ((i + 1) % (N_batch//10) == 0 or i == N_batch - 1) and idr_torch.rank == 0:
                print('Epoch [{}/{}], Step [{}/{}], Time: {:.3f}, Loss: {:.4f}, Acc:{:.4f}'.format(
                      epoch + 1, args.epochs, i+1, N_batch, chrono.tac_time(), loss.item(), np.mean(accuracies)))
                                                            #
                accuracies = []                             #*****************************************************

            # scheduler update
            scheduler.step()
            
            chrono.dataload()                               #*****************************************************
                                                            #
            #### VALIDATION ############                    #
            if ((i == N_batch - 1) or (args.test and i==args.test_nsteps-1)) and not args.findlr: 
                                                            #
                chrono.validation()                         #
                model.eval()                                #       ### DON'T MODIFY #############
                                                            #  
                for iv, (val_images, val_labels) in enumerate(val_loader):   
                                                            #*****************************************************
                    
                    # distribution of images and labels to all GPUs
                    # TODO

                    # Runs the forward pass with no grade mode.
                    with torch.no_grad():
                        val_outputs = model(val_images)
                        loss = criterion(val_outputs, val_labels)

                    val_loss += (loss * val_images.size(0) / N_val)      #*****************************************
                    _, predicted = torch.max(val_outputs.data, 1)        #
                    val_accuracy += ((predicted == val_labels).sum() / N_val)  ### DON'T MODIFY #######
                                                                         #
                    if args.test and iv >= 20: break                     #*****************************************
                                                    
                
                
                model.train()                                      #***********************************************
                chrono.validation()                                #
                                                                   #
                if not args.test and idr_torch.rank == 0:          #    
                    print('##EVALUATION STEP##')                   #    ### DON'T MODIFY ##############
                    print('Epoch [{}/{}], Validation Loss: {:.4f}, Validation Accuracy: {:.4f}'.format(epoch + 1, args.epochs,
                    val_loss.item(), val_accuracy.item()))         #
                    print(">>> Validation complete in: " + str(chrono.val_time))    
                                                                   #
                    wandb.log({"test accuracy": val_accuracy.item(),
                               "test loss":  val_loss.item()})     #***********************************************

                
                ## Clear validations metrics
                val_loss -= val_loss
                val_accuracy -= val_accuracy 
    
    if args.findlr:                                     #***********************************************************
        if idr_torch.rank == 0:                         #
            print(f'accuracies: {accuracies}')          #
            print(f'loss list: {losses}')               #
            print(f'learning rates: {lrs}')             #        ### DON'T MODIFY #############################
    else:                                               #
        chrono.display(N_val_batch)                     #
        if idr_torch.rank == 0:                         #
            print(">>> Number of batch per epoch: {}".format(N_batch)) 
            print(f'Max Memory Allocated {torch.cuda.max_memory_allocated()} Bytes') 
                                                        #*********************************************************** 

        
    # Save last checkpoint
    if not args.test and not args.findlr and idr_torch.rank == 0:
        checkpoint_path = f"checkpoints/{os.environ['SLURM_JOBID']}_{global_batch_size}.pt"
        torch.save(model.state_dict(), checkpoint_path)
        print("Last epoch checkpointed to " + checkpoint_path)
         

if __name__ == '__main__':
    
    # display info
    if idr_torch.rank == 0:
        print(">>> Training on ", len(idr_torch.hostnames), " nodes and ", idr_torch.size, " processes")
    main()
