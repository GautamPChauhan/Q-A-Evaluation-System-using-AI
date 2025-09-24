# function
def lagrange_interpolation(x, points):
    total = 0               # initialize the result of the interpolation
    n = len(points)          # number of given points
    for i in range(n):      # loop through each point to build the Lagrange basis polynomial
        xi, yi = points[i]      # xi = x-coordinate ane yi = y-coordinate of the i-th point
        Li = 1                      
        for j in range(n):          # aahi thi formula
            if j != i:
                xj, _ = points[j]
                Li *= (x - xj) / (xi - xj)
        total += yi * Li
    return total


# 4 point
points_4 = [(-1, -1), (-2, -9), (2, 11), (4, 69)]
print(f"f(5) ≈ {lagrange_interpolation(0, points_4):.5f}")

# 2 point
points_2 = [(0.1,0.09983), (0.2, 0.19867)]
print(f"f(0.15) ≈ {lagrange_interpolation(0.15, points_2):.5f}")