# Audit Report --- Issues Found + Corrections Made

## 1. Dataset Overview

Dataset: Evacuation Shelters (data.gov.tw)\
Purpose: Spatial analysis with AQI stations to evaluate shelter
suitability during poor air quality scenarios.

The dataset was inspected for coordinate validity, spatial consistency,
and missing attributes required for analysis.

------------------------------------------------------------------------

## 2. Issues Identified

### 2.1 Incorrect Coordinates

Several shelter points were located in unrealistic locations,
including: - Points appearing in the ocean - Points located outside
Taiwan (some within mainland China)

This indicates potential coordinate errors or data entry issues in the
original dataset.

### 2.2 Missing Facility Type Attribute

The dataset did not contain an attribute indicating whether shelters are
**indoor** or **outdoor**, which is important for evaluating exposure to
poor air quality.

------------------------------------------------------------------------

## 3. Corrections Applied

### 3.1 Spatial Validation Using Administrative Boundaries

To remove incorrect points, a spatial validation process was applied:

1.  An open-source Taiwan administrative boundary **SHP file** was
    obtained.
2.  Shelter point data was spatially intersected with the Taiwan
    administrative polygons.
3.  Only points that intersect with Taiwan administrative boundaries
    were retained.

This step removed shelters located outside Taiwan or in the ocean.

### 3.2 Indoor / Outdoor Inference

Because the dataset lacked indoor/outdoor attributes, a semantic
inference approach was used based on facility names.

Keyword rules used:

Indoor (True) - 圖書館 - 體育館 - 禮堂 - 活動中心 - 學校

Outdoor (False) - 公園 - 廣場

If the facility type could not be clearly identified, the shelter was
conservatively classified as **indoor**.

------------------------------------------------------------------------

## 4. Data Quality Outcome

After spatial validation and attribute inference:

-   Invalid coordinates were removed.
-   All shelters fall within Taiwan administrative boundaries.
-   An **is_indoor** attribute was added for scenario analysis.

These corrections ensure the dataset can be reliably used for the
spatial overlay and AQI risk analysis tasks.

------------------------------------------------------------------------

## 5. Notes

While AI tools were initially tested for automated coordinate
validation, they were not fully reliable in detecting geographic errors
such as ocean locations. Therefore, spatial intersection with
authoritative boundary data was used as the primary validation method.
