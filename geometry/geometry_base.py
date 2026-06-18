
def calculate_bezier_point(p0, p1, p2, p3, t):
    """
    Beregner et enkelt X- eller Y-koordinat langs en kubisk Bézier-kurve.
    p0, p1, p2, p3 er verdiene (f.eks. X eller Y) for kontrollpunktene.
    t er parameteren mellom 0.0 og 1.0.
    """
    return (1 - t)**3 * p0 + 3 * (1 - t)**2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3

def generate_curve_points(p0, p1, p2, p3, num_points=20):
    """
    Genererer en liste med punkter langs kurven fra t=0 til t=1.
    """
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        point_value = calculate_bezier_point(p0, p1, p2, p3, t)
        points.append(point_value)
    return points
