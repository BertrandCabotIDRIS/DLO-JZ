# FORMATION DLO-JZ : Deep Learning optimisé sur Jean Zay

Depôt pour la formation IA avancée dédiée à Jean ZAy

## Plan de Formation

Cette formation/atelier est dédiée au passage à l'echelle multi GPU / noeuds d'un code IA (Deep Learning). L'atelier se fera autour d'un code d'apprentissage Imagenet, dont le but sera d'accélérer le plus possible la phase d'entrainement.   

### Jour 1
* Présentation, Jean Zay, les enjeux du DL, accélération GPU + 3 TP : **2H**
* Distribution, Parallélisme de données, Dataloader + 2 TP : **2H30**
* Profiler + 1 TP : **1H30**

### Jour 2
* large batch, lr scheduler, optimiseurs + 1 TP : **3H**
* Visualisation de résultat sur Weight and Biases : **45min**
* parallélisme avancé, Deepspeed + 1 TP : **2H15**


**Formation prévu le 20, 21, 22 avril 2022**

Repétition en interne prévu:
* Le vendredi 11 fevrier: Presentation de la formation, Presentation de Jean ZAy, L'acceleration GPU et la mixed Precision
* Le mercredi 16 fevrier : Profiling, Distribution (Data Parallelism), Data Loader
* Le vendredi 25 fevrier : bonnes pratiques pour les aprentissages large batch, learning rate scheduler, optimiseurs, Weight and Biases
* Le vendredi 4 mars :  Distribution avancée, optiomisation des labels, Deep speed, modèles avancés, Bilan


# Fiche descriptive

# DLO-JZ (Deep Learning Optimisé sur Jean Zay)

## Responsable :
Bertrand Cabot

## Objectif :
Cette formation a pour objectif de passer en revue les principales techniques actuelles d'optimisation d'un apprentissage machine en Deep Learning, avec pour objectif le passage à l'échelle d'un supercalculateur. Les problématiques associées d'accélération et de distribution sur plusieurs GPU seront abordées, d'un point de vue système et algorithmique.

## Public concerné :
Cette formation s'adresse aux utilisateurs·rice·s IA de Jean Zay ou aux personnes qui maîtrisent les fondamentaux du Deep Learning et qui souhaitent se former aux enjeux du passage à l'échelle d'un supercalculateur.

## Pré-requis :
Les pré-requis nécessaires sont :
* de maîtriser les notions de l'apprentissage en Deep Learning
* de maîtriser le langage Python
* d'avoir des bases en PyTorch pour le bon déroulement des TP

## Durée :
2 jours.

## Contenu de la formation :
Cette formation est dédiée au passage à l'échelle multi-GPU de l'entraînement d'un modèle en Deep Learning. 
Le fil conducteur des aspects pratiques de la formation est la mise à l'échelle optimisée (accélération, distribution) d'un entraînement d'un modèle sur la base de donnée Imagenet. Pour cela, les participant·e·s seront amené.e.s à coder et soumettre leurs calculs en appliquant les différentes notions abordées pendant les parties de cours. 

## Plan :

### Jour 1
   - Introduction
   - Jean Zay
   - Les enjeux de l'optimisation du *Deep Learning*
   - L'accélération GPU
   - La précision mixte
   - Le parallélisme de données 
   - L'optimisation du pré-traitement des données
   - Le *profiler* PyTorch

### Jour 2
   - La gestion des *large batches*
   - Les *learning rate schedulers*
   - Les optimiseurs
   - L'outil de visualisation *Weight and Biases*
   - Les parallélismes de modèle
   - La librairie d'optimisation *Deepspeed*

## Équipement :
Les parties pratiques se dérouleront sur le supercalculateur Jean Zay de l'IDRIS.


## Intervenants :
- Bertrand Cabot
- Myriam Peyrounette
- Bruno Tessier

## S’inscrire à cette formation :
https://cours.idris.fr
