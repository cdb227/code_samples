import numpy as np
import matplotlib.pyplot as plt
from scipy import stats



def is_root(fa, fb):
    # helper function to determine if f(a) and f(b) cross zero.
    return fa * fb < 0 # True if root, False if not.

##### First Derivative of Gaussian KDE PDF
def first_deriv_pdf(x, mu, s):
    """
    Evaluate the first derivative of a Gaussian Kernel Density Estimation (KDE) at x.

    Parameters:
        x (float): point at which to evaluate the first derivative.
        mu (array-like): Points being used to fit KDE, each fit with a normal distribution
        s (float): KDE bandwidth (smoothing)

    Returns:
        float: Value of the first derivative at point x.
    """
    N = len(mu)
    fact = -(1 / (((2 * np.pi) ** 0.5) * N * s ** 3.))
    xmm = x - mu
    return fact * (np.exp(-((xmm) ** 2.) / (2 * s ** 2.)) * xmm).sum(axis=0)

def recursive_rootfinding(a, b, tol, fargs, f=first_deriv_pdf):
    """
    Recursively find roots of a function within a given interval.

    Parameters:
        a (float): Lower bound of the interval.
        b (float): Upper bound of the interval.
        tol (float): Tolerance level for root determination.
        fargs (tuple): Additional arguments to be passed to the function f.
        f (function): Function to be evaluated.

    Returns:
        list: List of roots within the given interval.
    """
    roots = []  # Save roots
    mp = (b + a) / 2.  # Midpoint
        
    if (b - a) > tol:  # Not within tolerance, refine search
        roots += recursive_rootfinding(a, mp, tol, fargs)  # Check left side
        roots += recursive_rootfinding(mp, b, tol, fargs)  # Check right side 
    else:  # Within tolerance, determine if root or not
        if is_root(f(a, *fargs), f(b, *fargs)):  # Use midpoint as root
            return [mp]
        else:  # Not a root
            return []
    
    return roots

#generate a synthetic bimodal distribution to find roots on
n=2000 # n for each sample

m1, s1 = 2, 1 #mean, sigma
m2, s2 = -2, 1 #mean, sigma

samp1 = np.random.normal(loc=m1, scale=s1, size=n)
samp2 = np.random.normal(loc=m2, scale=s2, size=n)
ss= np.concatenate((samp1,samp2))

# Plot the distributions
fig=plt.figure(figsize=(5, 5))
#plot histogram of samples
plt.hist(ss, bins =100, alpha=0.5, color='blue', density=True, label = 'Samples')
#fit a kernel density estimate (KDE) to distribution
kde= stats.gaussian_kde(ss)
p = np.linspace(-5,5,1000)
plt.plot(p, kde(p), color = 'k', linestyle='--', lw=3)

#find roots of KDE using recursive rootfinding algo.
bw = 0.45730505192732634 * np.std(ss) #use Scott's Rule for bandwidth smoothing
roots = recursive_rootfinding(np.min(ss), np.max(ss), tol=bw/10, fargs=(ss, bw))
#plot roots
plt.scatter(roots, kde(roots), color ='tab:red',s=100,zorder=2, label='roots')


plt.xlabel('x')
plt.ylabel('Density')
plt.legend()
plt.grid(True)
fig.savefig('./root_finding.png')
plt.show()