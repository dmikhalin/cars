# Гонки

Создайте своего бота для управления гоночной машинкой.
В папке [player_demo/](player_demo/) находится шаблон. 
Измените в файле [bot.py](player_demo/bot.py) функцию move(), 
чтобы она возвращала новую скорость вашей машинки.

Если хотите не просто писать бота вслепую, а запустить 
визуализацию локально, используйте файл [local_test.py](local_test.py).
Не забудьте установить две необходимых библиотеки.

Пример поля, которое на вход получает бот:

    #######################FFFFFF#
    #...................###......#
    #...................###......#
    #...................###......#
    #...................###......#
    #...................###......#
    #...................###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #........###........###......#
    #...CC...###.................#
    #.C..C..C###.................#
    #SSSSSSCS###.................#
    ##############################

Несколько уточнений по авариям:

1. Машины сталкиваются только в конечных точках своих перемещений: если
пересекаются траектории, ничего страшного не происходит. Но траектория
движения не должна пересекать границы поля.
2. На финише столкновений между машинами не бывает.
3. После аварии машины какое-то время не могут ехать дальше. Каждый такт
случайное число от 0 до 1 сравнивается с параметром level у игрока, и если
оно оказывается больше level, то ремонт заканчивается, и можно ехать дальше.