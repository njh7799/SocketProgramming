import re

#Check if the string starts with "The" and ends with "Spain":

txt = "/kill meth3doa4 sADASDa"
x = re.findall("\/kill ([\w]+)", txt)

print(x)
