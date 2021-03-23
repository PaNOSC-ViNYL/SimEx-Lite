# %%
with open('requirements.txt') as readme_file:
    readme = readme_file.read()
    mylist = readme.split()
    print(mylist)