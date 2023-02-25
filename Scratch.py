start = 10000
rate = 1.04

for i in range(52):

    start = start * rate
    if i % 4 == 0 and i < 24:
        start += 5000
print(start)


