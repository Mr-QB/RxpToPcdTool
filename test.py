with open("times.txt", "r") as f:
    line_count = sum(1 for line in f)
print(line_count)
