nums = [4,1,2,1,2]

# print(d)

dict = {}
for i in nums:
    dict[i] = 0
for i in nums:
    dict[i] += 1

a = list (dict.keys()) [list (dict.values()).index (1)]
print(a)