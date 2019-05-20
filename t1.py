from random import randint
fund = 1000
game_round = 1
dice = randint(2,12)
while fund > 0:
    debt = int(input('your debt: '))
    if game_round == 1:
        if dice == 7 or dice == 11:
            fund += debt
        elif dice == 2 or dice == 3 or dice == 12:
            fund -= debt
        else:

            continue
        game_round += 1


