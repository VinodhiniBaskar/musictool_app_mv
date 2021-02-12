import numpy as np
from sklearn.cluster import DBSCAN
import statistics

# This function will help us when segmentation data about objects is present.
# Takes all points found on image as an argument. Not used now.
def frame_postprocessing(points, the_coefficient):
    if not points.shape[0]:
        return np.array([])
    db = DBSCAN(eps=0.06, min_samples=12/the_coefficient,  n_jobs=-1).fit(points)

    labels = np.array(db.labels_)

    result = np.array([])
    cluster_set = set(labels)
    clusters = []
    clusters_volumes = []
    for c in cluster_set:
        if c == -1:
            continue
        ci = points[labels == c]
        clusters_volumes.append(len(ci))
        clusters.append(ci)

    clusters = np.array(clusters)
    clusters_volumes = np.array(clusters_volumes)
    if len(clusters_volumes):
        median_volume = statistics.median(clusters_volumes)
        result = clusters[clusters_volumes > median_volume*0.8]
    return result





