import re

text = "she sells seashells she by the seashore"
matches = re.findall(r'(\w+)lls', text)
print(matches)  # ['seashells', 'the']
