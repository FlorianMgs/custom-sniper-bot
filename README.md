## Usage
```
sniper.py -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3 -a 0.2 -tp 15
```

Il n'y a que le TP qui est disponible pour le moment, je n'ai toujours pas checké SL/TSL, enjoy ;)

## Mesures antibots
J'ai add une feature qui permet de detecter dans la mempool si une certaine fonction a été trigger sur le token visé.
Par exemple, si il y a une fonctin disableAntibot sur le smart contract visé, tu la fout dans settings.json:
```
function: disableAntibot()
```
Si il y a des arguments, il faut ajouter seulement leur type, et non pas leur noms. Exemple:
```
function: disableAntibot(bool)
```
Ensuite, qd tu run le snipe, il faut ajouter l'argument -wf:
```
sniper.py -t 0x34faa80fec0233e045ed4737cc152a71e490e2e3 -a 0.2 -tp 15 -wf
```
Comment ça marche ?
Une fonction asynchrone va écouter la mempool à la recherche des événements liés au token visé. On check dans le champ "input" de la transaction à la recherche de la signature héxadécimale de la fonction définie dans settings.py.
Si detecté, le buy est trigger.
 
