def get_regions_of_interest(high_text_density):
    if not high_text_density:
        return [
            {
                "BoundingBox": {
                    "Width": 1,
                    "Height": 1,
                    "Left": 0,
                    "Top": 0
                }
            }
        ]

    return [
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.22,
                "Left": 0,
                "Top": 0
            }
        },
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.22,
                "Left": 0,
                "Top": 0.2
            }
        },
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.22,
                "Left": 0,
                "Top": 0.4
            }
        },
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.22,
                "Left": 0,
                "Top": 0.5
            }
        },
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.22,
                "Left": 0,
                "Top": 0.7
            }
        },
        {
            "BoundingBox": {
                "Width": 1,
                "Height": 0.2,
                "Left": 0,
                "Top": 0.8
            }
        }
    ]


def implode_regions(pieces):
    result = []
    for piece in pieces:
        result.extend(piece['Result']['TextDetections'])
    return result
