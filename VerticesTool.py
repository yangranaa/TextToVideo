# 顶点数据
import numpy as np
from scipy.spatial import  Delaunay

screen_vertices = np.array([
        [-1.0, 1.0, 0.0, 0.0, 1.0],
        [-1.0, -1.0, 0.0, 0.0, 0.0],
        [1.0, 1.0, 0.0, 1.0, 1.0],
        [1.0, -1.0, 0.0, 1.0, 0.0],
    ], dtype=np.float32)

def fill_point(vertices, point_len):

    result = np.empty((len(vertices), point_len), dtype=np.float32)

    result[:, :len(vertices[0])] = vertices
    result[:, len(vertices[0]):point_len] = 0

    return result


def broken_3d_mesh(vertices, inter_points):
    # 随机生成内部顶点
    num_internal_points = inter_points
    internal_points = np.random.rand(num_internal_points, len(vertices[0])) * 2 - 1
    internal_points[:, 2] = 0
    internal_points[:, 3] = internal_points[:, 0] * 0.5 + 0.5
    internal_points[:, 4] = internal_points[:, 1] * -0.5 + 0.5

    # 合并边界顶点和内部顶点
    all_points = np.concatenate([vertices, internal_points])

    # 生成 Delaunay 三角剖分
    tri = Delaunay(all_points[:, :3])

    # 获取四面体的顶点索引
    tetrahedra = tri.simplices

    # 提取四面体的表面三角形
    result = None
    tri_ids = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
    for tetra in tetrahedra:
        avg_vec = np.mean(all_points[tetra, :3], axis=0)
        # 每个四面体有4个面，每个面是一个三角形
        for face in tri_ids:
            tetra_points = [all_points[tetra[ids]] for ids in face]
            point_in_back = [point for point in tetra_points if point[2] > 0]
            if len(point_in_back) == 1:
                font_point = [point for point in tetra_points if point[2] <= 0]
                point_in_back[0][3:5] = font_point[0][3:5]
            elif len(point_in_back) == 2:
                font_point = [point for point in tetra_points if point[2] <= 0]
                point_in_back[0][3:5] = font_point[0][3:5]
                point_in_back[1][3:5] = font_point[0][3:5]
            # elif len(point_in_back) == 3:
            #     point_in_back[0][3:5] = [0, 0]
            #     point_in_back[1][3:5] = [0, 0]
            #     point_in_back[2][3:5] = [0, 0]

            for point in tetra_points:
                point[5:] = avg_vec

            if result is None:
                result = np.concatenate([tetra_points[:]])
            else:
                result = np.concatenate([result[:], tetra_points[:]], dtype=np.float32)

    #
    # for point in result:
    #     print(point)
    return result

# tes_vertices = np.array([
#     [-1.0, -1.0, 0.5, 0.0, 1.0],
#     [-1.0, -1.0, -0.5, 0.0, 1.0],
#     [1.0, -1.0, 0.5, 1.0, 1.0],
#     [1.0, -1.0, -0.5, 1.0, 1.0],
#     [1.0, 1.0, 0.5, 1.0, 0.0],
#     [1.0, 1.0, -0.5, 1.0, 0.0],
#     [-1.0, 1.0, 0.5, 0.0, 0.0],
#     [-1.0, 1.0, -0.5, 0.0, 0.0],
# ], dtype=np.float32)
#
# broken_3d_mesh(fill_point(tes_vertices, 8), 0)

def set_group_rot_point(vertices):
    for i in range(0, len(vertices), 3):
        if i + 2 >= len(vertices):
            break

        vec = np.mean(vertices[[i, i + 1, i + 2], :3], axis=0)

        vertices[[i, i + 1, i + 2], 5:8] = vec


def broken_2d_mesh(vertices, inter_points):
    # 随机生成内部顶点
    num_internal_points = inter_points
    internal_points = np.random.rand(num_internal_points, len(vertices[0])) * 2 - 1
    internal_points[:, 2] = 0.0  # 确保 z 坐标为 0
    internal_points[:, 3] = internal_points[:, 0] * 0.5 + 0.5
    internal_points[:, 4] = internal_points[:, 1] * 0.5 + 0.5

    # 合并边界顶点和内部顶点
    all_points = np.concatenate([vertices, internal_points])

    # 生成 Delaunay 三角剖分
    tri = Delaunay(all_points[:, :2])  # :2只使用 x 和 y 坐标进行三角剖分

    result = np.empty( (len(tri.simplices)*3,len(vertices[0])), dtype=np.float32)
    idx = 0
    for triangle in tri.simplices:
        result[[idx,idx+1,idx+2]] = all_points[triangle]
        idx += 3

    return result


def generate_triangle_strip_vertices(horizontal_points, vertical_points, h_step, v_step):
    """
    生成适用于 GL_TRIANGLE_STRIP 的顶点数组

    参数:
        horizontal_points (int): 横向顶点数
        vertical_points (int): 纵向顶点数
        h_step (float): 横向步长
        v_step (float): 纵向步长

    返回:
        np.ndarray: 顶点数组，形状为 (K, 3)，每行表示一个点的xyz坐标
    """
    # 生成原始网格点
    x = np.linspace(0, (horizontal_points - 1) * h_step, horizontal_points)
    y = np.linspace(0, (vertical_points - 1) * v_step, vertical_points)
    X, Y = np.meshgrid(x, y, indexing='xy')
    grid = np.column_stack((X.ravel(), Y.ravel(), np.zeros_like(X.ravel())))

    # 重组顶点顺序为 GL_TRIANGLE_STRIP
    vertices = []
    for row in range(vertical_points - 1):
        for col in range(horizontal_points):
            # 当前行顶点
            current_idx = row * horizontal_points + col
            vertices.append(grid[current_idx])

            # 下一行对应位置顶点
            next_idx = (row + 1) * horizontal_points + col
            vertices.append(grid[next_idx])

        # 插入退化三角形（行末添加重复顶点）
        if row < vertical_points - 2:
            vertices.append(grid[next_idx])
            vertices.append(grid[(row + 1) * horizontal_points])

    return np.array(vertices)

def trans_draw_ver(vertices):
    vertices = fill_point(vertices, 5)

    vertices[:, 0] = vertices[:, 0] * 2 - 1
    vertices[:, 1] = vertices[:, 1] * 2 - 1
    vertices[:, 3] = vertices[:, 0] * 0.5 + 0.5
    vertices[:, 4] = vertices[:, 1] * 0.5 + 0.5

    return vertices