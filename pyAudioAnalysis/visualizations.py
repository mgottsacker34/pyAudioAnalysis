"""
This Python script is what we will use to formulate visualizations on after a meeting has been segmented and evaluated.

"""
import matplotlib.pyplot as mp

labels = 'Male', 'Female'
sizes = [60, 40]
#explode = (0, 0)     #this command emphasizes a slice

fig0, ax0 = mp.subplots()
ax0.pie(sizes,labels=labels, autopct='%1.1f%%',
        shadow=False, startangle=180)

ax0.axis('equal')   #Equal aspect ratio ensures that pie is drawn as circle

mp.title('Segmented Evaluation')

"""
This piece is now for the ground truth

mp.figure(1)
groundTruth = 'Male', 'Female', 'Silence'
sizesGT = [30,30,40]
fig1,ax1 = mp.subplots()
ax1.pie(sizesGT,labels=groundTruth, autopct='%1.1f%%',
        shadow=False, startangle=180)
ax1.axis('equal')
#fig1.title('Ground Truth')
"""
mp.show()
