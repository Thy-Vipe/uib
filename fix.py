
with open("H:\ProgrammingProjects\GUI_tools\objnames.txt", "r") as file:
	words = file.readlines()
	new = []
	for word in words:
		if "'s" not in word:
			new.append(word)

with open("H:\ProgrammingProjects\GUI_tools\objNames.uibsrc", "w") as newfile:
	newfile.writelines(new)