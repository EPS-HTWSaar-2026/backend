import numpy 
from numpy import sqrt, dot, cross
from numpy.linalg import norm

ANCHORS = {
    "ESP1": numpy.array([0.0, 0.0, 0.0]),
    "ESP2": numpy.array([5.0, 7.0, 0.0]),
    "ESP3": numpy.array([2.5, 4.3, 0.0]),
    }

MAC_TO_ESP = {
    "AA:BB:CC:DD:EE:01": "ESP1",
    "AA:BB:CC:DD:EE:02": "ESP2",
    "AA:BB:CC:DD:EE:03": "ESP3",
    }
 
RSSI_REF = -59   
PATH_LOSS_N = 3  

latest_rssi = {esp: None for esp in ANCHORS}

def rssi_to_distance(rssi, rssi_ref = RSSI_REF, n = PATH_LOSS_N):
    r = 10 ** ((rssi_ref - rssi) / (10 * n))
    return r

def update_from_rssi(mac, rssi):
    esp = MAC_TO_ESP.get(mac)
    if esp:
        latest_rssi[esp] = rssi
        print(f"Updated {esp} with RSSI: {rssi}")
    else:
        print(f"Unknown MAC address: {mac}")
        return None
    
def all_rssi_received():
    return all(rssi is not None for rssi in latest_rssi.values())

def trilaterate(p1, p2, p3, r1, r2, r3):
    temp1 = p2 - p1
    e_x = temp1 / norm(temp1)

    temp2 = p3 - p1
    i = dot(e_x, temp2)

    temp3 = temp2 - i * e_x
    e_y = temp3 / norm(temp3)

    e_z = cross(e_x, e_y)

    d = norm(p2 - p1)
    j = dot(e_y, temp2)

    x = (r1*r1 - r2*r2 + d*d) / (2*d)
    y = (r1*r1 - r3*r3 - 2*i*x + i*i + j*j) / (2*j)

    temp4 = r1*r1 - x*x - y*y

    if temp4 < 0:
        raise Exception("The three spheres do not intersect!")

    z = sqrt(temp4)

    p = p1 + x*e_x + y*e_y + z*e_z

    return p

def compute_error(point, p1, p2, p3, r1, r2, r3):
    d1 = norm(point - p1)
    d2 = norm(point - p2)
    d3 = norm(point - p3)

    residuals = numpy.array([
        d1 - r1,
        d2 - r2,
        d3 - r3
    ])

    rmse = sqrt(numpy.mean(residuals**2))
    confidence_radius = numpy.max(numpy.abs(residuals))

    return residuals, rmse, confidence_radius

def locate_tag():
    p1 = ANCHORS["ESP1"]
    p2 = ANCHORS["ESP2"]
    p3 = ANCHORS["ESP3"]

    r1 = rssi_to_distance(latest_rssi["ESP1"])
    r2 = rssi_to_distance(latest_rssi["ESP2"])
    r3 = rssi_to_distance(latest_rssi["ESP3"])

    print(f"Estimated distances: {r1:.2f}, {r2:.2f}, {r3:.2f}")

    point = trilaterate(p1, p2, p3, r1, r2, r3)
    residuals, rmse, confidence = compute_error(point, p1, p2, p3, r1, r2, r3)

    print("\n Estimated position:")
    print(point)

    print("\n Residuals (error per ESP):")
    print(f"ESP1: {residuals[0]:+.4f}")
    print(f"ESP2: {residuals[1]:+.4f}")
    print(f"ESP3: {residuals[2]:+.4f}")

    print(f"Confidence radius: ±{confidence:.4f} m")

    return point, rmse, confidence

if __name__ == "__main__":
    packets = [
        ("AA:BB:CC:DD:EE:01", -79),  
        ("AA:BB:CC:DD:EE:02", -83),   
        ("AA:BB:CC:DD:EE:03", -76),   
        ]
 
    print("── Incoming packets ──")
    for mac, rssi in packets:
        update_from_rssi(mac, rssi)
 
    locate_tag()

