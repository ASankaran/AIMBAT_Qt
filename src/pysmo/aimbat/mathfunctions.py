import numpy as np

def l1norm(x):
	return np.sum(np.absolute(x))

def l2norm(x):
	return np.sqrt(np.sum(np.absolute(x)**2))