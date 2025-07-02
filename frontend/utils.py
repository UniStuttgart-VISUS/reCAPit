import numpy as np
import logging

from qpsolvers import solve_qp, available_solvers
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter



def linear_layout(target_loc, elem_width, min_xpos, max_xpos):
    target_loc = np.array(target_loc)
    """
    print()
    print(target_loc)
    print(elem_width)
    print(max_xpos)
    print()
    """
    count = len(target_loc)
    d = target_loc

    # Constraint least squares: min || x - q ||
    P = np.eye(count)
    q = -target_loc

    # Inequality lhs: Distance between adjacent elements
    G = np.eye(N=count) + np.diag(np.ones(count-1) * -1, k=1)
    # For the last element there is no next element
    G[count-1, count-1] = -1

    # Inequality rhs: Minimum distance between adjacent elements
    h = np.array(elem_width) * -1
    #h = np.ones(count) * elem_width * -1

    # Positions are bounded between provided min and max pos
    lb = np.ones_like(d) * min_xpos
    ub = np.ones_like(d) * max_xpos

    if len(available_solvers) == 0:
        logging.error('No qpsolvers installed!')
        return np.zeros_like(target_loc)
    elif 'proxqp' in available_solvers:
        solver = 'proxqp'
    else:
        solver = available_solvers[0]

    x = solve_qp(P, q, G, h, lb=lb, ub=ub, solver=solver)
    return x


def longest_common_substring(s1, s2):
    # Get lengths of both strings
    m, n = len(s1), len(s2)

    # Create a 2D table to store lengths of longest common suffixes
    # Initialize all values to 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Length of the longest common substring
    length = 0

    # Variable to store the end point of the longest common substring in s1
    end_point_1 = 0
    end_point_2 = 0

    # Build the table in bottom-up fashion
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > length:
                    length = dp[i][j]
                    end_point_1 = i
                    end_point_2 = j
            else:
                dp[i][j] = 0

    return {'a': end_point_1 - length, 'b': end_point_2 - length, 'size': length}


def blend_images(image1, image2, opacity=0.5):
    """
    Blends two QImage objects together.

    :param image1: The base QImage.
    :param image2: The QImage to blend on top of the base image.
    :param opacity: The opacity of the second image (0.0 to 1.0).
    :return: A new QImage with the blended result.
    """
    # Ensure both images are the same size
    if image1.size() != image2.size():
        raise ValueError('Images need to be same size!')

    # Create a new QImage to store the result
    result = QImage(image1.size(), QImage.Format.Format_ARGB32)
    #result.fill(QColor("transparent"))
    result.fill(Qt.GlobalColor.transparent)

    # Create a QPainter to blend the images
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

    # Draw the first image
    painter.drawImage(0, 0, image1)

    # Set the opacity for the second image
    painter.setOpacity(opacity)

    # Draw the second image on top of the first
    painter.drawImage(0, 0, image2)

    # Finish painting
    painter.end()

    return result


