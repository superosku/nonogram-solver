
# This is a nonogram solver

Features
 - Solves most nonograms fastly (even ~100x100 can be solved in few minutes, depending on the nonogram).
 - Solves also unambiguous nonograms by guessing a step with recursive search when fast search does not yield results. After guessing one row, returns to fast search. Continues fast search until stuck again and does recursive guess when stuck again.

Some of the machine readable nonograms taken from here
https://github.com/ThomasR/nonogram-solver
And here
https://github.com/LKonsta/Tiralabra2020-NonogramSolver

Example output of solved nonogram:

```
               122246121115311
                     2 5
               111233 3 97311

                121     33 11

                 11





 1,3             #     ###
 2,2            ##     ##
 2,3              ##    ###
 2,1,2            ##  # ##
 1,3                  # ###
 2,3                 ## ###
 2,4                 ## ####
 3,4                ### ####
 4,5               #### #####
 5,5              ##### #####
 3,6                ### ######
 2,1,1           ##   # #
 12               ############
 8                  ########
 15             ###############
 ```


