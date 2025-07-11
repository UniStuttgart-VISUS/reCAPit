import numpy as np
import logging
import cvxpy as cp

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter


def linear_layout(target_loc, elem_width, min_xpos, max_xpos):
    target_loc = np.array(target_loc)
    count = len(target_loc)
    d = target_loc

    # Decision variable
    x = cp.Variable(count)

    # Objective: minimize ||x - target_loc||^2
    objective = cp.Minimize(cp.sum_squares(x - d))

    # Inequality constraints: x[i+1] - x[i] >= elem_width
    constraints = [x[i + 1] - x[i] >= elem_width for i in range(count - 1)]

    # Bounds
    constraints += [x >= min_xpos, x <= max_xpos]

    # Problem definition and solving
    prob = cp.Problem(objective, constraints)
    prob.solve()

    if x.value is None:
        logging.error('No valid layout found. Quadratic program has no solution.')
        return np.zeros_like(target_loc)

    return x.value


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


