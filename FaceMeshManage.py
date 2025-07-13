
import mediapipe as mp

import numpy as np
from scipy.spatial import Delaunay

from ImageTool import adjust_img
from Setting import Setting

class FaceMeshManage:

    vertices = np.array([
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ], dtype=np.float32)

    face_mesh = mp.solutions.face_mesh

    sfs = None

    dfs = None

    # refine_landmarks True：额外生成眼周、唇周等高精度关键点（总关键点数增至 478 个）
    def __init__(self, src_path):
        if FaceMeshManage.sfs is None:
            FaceMeshManage.sfs = FaceMeshManage.face_mesh.FaceMesh(static_image_mode=True,
                               max_num_faces=1,
                               refine_landmarks=True,
                               min_detection_confidence=0.7)
        if FaceMeshManage.dfs is None:
            FaceMeshManage.dfs = FaceMeshManage.face_mesh.FaceMesh(static_image_mode=False,
                                  max_num_faces=1,
                                  refine_landmarks=True,
                                  min_detection_confidence=0.7)

        self.face_offset_z = Setting.get('face_offset_z')
        self.test_idx = Setting.get('test_idx')
        self.test_z = Setting.get('test_z')
        self.mid_idx = Setting.get('mid_idx')
        self.left_idx = Setting.get('left_idx')
        self.right_idx = Setting.get('right_idx')
        self.left_oval = Setting.get('left_oval')
        self.right_oval = Setting.get('right_oval')

        self.src_img = adjust_img(src_path)
        self.src_pts = self.get_face_pts(self.sfs, self.src_img)

    def get_face_pts(self, face_mesh, img):
        result = face_mesh.process(img)
        face_pts = None
        if result.multi_face_landmarks:
            face_nl_pts = result.multi_face_landmarks[0].landmark
            face_pts = np.array([[lm.x, lm.y, lm.z] for lm in face_nl_pts])

            # debug_img = img.copy()
            # src_hull = cv2.convexHull(face_pts.astype(np.int32))
            # cv2.polylines(debug_img, [src_hull.astype(np.int32)], True, (0, 255, 0), 2)
            # cv2.imshow("src", debug_img)
        # else:
        #     MyLog.error("识别不到人脸")

        return face_pts

    def get_face_map_vertx(self, img):

        face_pts = self.get_face_pts(self.dfs, img)

        if face_pts is not None:
            second_column = face_pts[:, 2]
            max_z = np.max(second_column)
            min_z = np.min(second_column)

            mid_x = face_pts[self.mid_idx, 0]
            left_len = max(mid_x - face_pts[self.left_idx, 0], 1e-10)
            right_len = max(face_pts[self.right_idx, 0] - mid_x, 1e-10)

            if left_len < right_len:
                rate = left_len / right_len
                no_fade = self.right_oval
            else:
                rate = right_len / left_len
                no_fade = self.left_oval

            rate = rate +  (1 - rate) * self.face_offset_z #math.pow(rate, self.face_fade_z)
            z_size = max_z - min_z
            face_fade_z = min_z + z_size * rate
            # nose_fade_z = max_z - z_size * self.test_z

            mask = second_column < face_fade_z
            # mask[self.test_idx] = face_pts[self.test_idx, 2] < nose_fade_z
            mask[no_fade] = True

            ids = np.where(mask)[0]

            # kd_tree = KDTree(face_nl_pts)
            # pairs = kd_tree.query_pairs(0.004)

            # keep_mask = np.ones(face_nl_pts.shape[0], dtype=bool)
            # for i, j in pairs:
            #     keep_mask[j] = False
            # ids = np.where(keep_mask)[0]

            pts_len = len(ids)  # face_nl_pts.shape[0]##

            vertices = np.empty((pts_len + 6, 5), dtype=np.float32)
            vertices[:pts_len, :3] = face_pts[ids]
            vertices[:pts_len, 3:5] = self.src_pts[ids, :2]
            vertices[pts_len:, :] = FaceMeshManage.vertices

            tris = Delaunay(vertices[:, :2])
            vertices = vertices[tris.simplices.reshape(-1)]
        else:
            vertices = FaceMeshManage.vertices

        return vertices
