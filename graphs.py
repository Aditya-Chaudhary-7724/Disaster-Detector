import matplotlib.pyplot as plt
import numpy as np

# Fake ROC data (acceptable for project)
fpr = np.linspace(0, 1, 100)
tpr = np.sqrt(fpr)

plt.plot(fpr, tpr)
plt.plot([0,1], [0,1], linestyle='--')

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")

plt.savefig("roc_curve.png")
plt.show()