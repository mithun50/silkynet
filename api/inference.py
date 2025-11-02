"""
SilkyNet Inference Module
Refactored for API usage
"""

import numpy as np
import cv2
from keras.models import load_model
import keras.backend
from PIL import Image
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed


class SilkyNetInference:
    """
    SilkyNet inference engine for silkworm segmentation and counting
    """

    def __init__(self, model_path, img_size=(512, 512)):
        """
        Initialize the inference engine

        Args:
            model_path: Path to trained U-Net model (.hdf5)
            img_size: Input image size (width, height)
        """
        self.img_size = img_size
        self.model = self._load_model(model_path)

    def _load_model(self, model_path):
        """Load the trained model with custom objects"""
        custom_objects = {'dice_coef': self.dice_coef}
        return load_model(model_path, custom_objects=custom_objects)

    @staticmethod
    def dice_coef(y_true, y_pred):
        """Dice coefficient metric"""
        smooth = 1e-4
        y_true_f = keras.backend.flatten(y_true)
        y_pred_f = keras.backend.flatten(y_pred)
        intersection = keras.backend.sum(y_true_f * y_pred_f)
        score = (2. * intersection + smooth) / (
            keras.backend.sum(y_true_f) + keras.backend.sum(y_pred_f) + smooth
        )
        return score

    def preprocess_image(self, image):
        """
        Preprocess PIL Image for model input

        Args:
            image: PIL Image object

        Returns:
            Preprocessed numpy array
        """
        # Resize to model input size
        image_resized = image.resize(self.img_size)

        # Convert to array and normalize
        image_arr = np.array(image_resized).astype(np.float32) / 255.0

        # Add batch dimension
        return np.expand_dims(image_arr, axis=0)

    def segment(self, image):
        """
        Perform segmentation on image

        Args:
            image: PIL Image object

        Returns:
            Binary mask (numpy array)
        """
        # Preprocess
        input_arr = self.preprocess_image(image)

        # Predict
        mask_pred = self.model.predict(input_arr, verbose=0)

        # Remove batch dimension and threshold
        mask = (mask_pred[0, :, :, 0] > 0.5).astype(np.uint8)

        return mask

    def count_contours(self, mask, threshold=200):
        """
        Count silkworms using contour detection

        Args:
            mask: Binary segmentation mask
            threshold: Threshold for binarization (0-255)

        Returns:
            Dictionary with counting results
        """
        # Convert to uint8 for OpenCV
        mask_uint8 = (mask * 255).astype(np.uint8)

        # Threshold
        _, thresh_img = cv2.threshold(mask_uint8, threshold, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, hierarchy = cv2.findContours(
            thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            return {
                'total_count': 0,
                'individual_count': 0,
                'overlapped_count': 0,
                'partial_count': 0,
                'artifacts_count': 0,
                'contours': contours
            }

        # Calculate contour areas
        contour_areas = np.array([cv2.contourArea(cnt) for cnt in contours])

        # Calculate median area
        median_area = np.median(contour_areas)

        # Classify contours
        artifacts = 0
        partial = 0
        overlapped = 0
        overlapped_contours = []

        for i, area in enumerate(contour_areas):
            if area < 0.2 * median_area:
                artifacts += 1
            elif 0.2 * median_area <= area < 0.5 * median_area:
                partial += 1
            elif area > 1.0 * median_area:
                overlapped += 1
                overlapped_contours.append(contours[i])

        # Separate overlapped larvae using watershed
        additional_count = self._separate_overlapped(
            thresh_img, overlapped_contours
        ) if overlapped_contours else 0

        # Calculate total
        individual = len(contours) - artifacts - overlapped
        total_count = individual + additional_count + partial

        return {
            'total_count': int(total_count),
            'individual_count': int(individual),
            'overlapped_count': int(overlapped),
            'additional_separated': int(additional_count),
            'partial_count': int(partial),
            'artifacts_count': int(artifacts),
            'contours': contours,
            'median_area': float(median_area)
        }

    def _separate_overlapped(self, mask, overlapped_contours):
        """
        Use watershed algorithm to separate overlapped larvae

        Args:
            mask: Binary mask
            overlapped_contours: List of overlapped contours

        Returns:
            Additional count from separated larvae
        """
        try:
            # Create image with only overlapped contours
            overlap_img = np.zeros_like(mask)
            cv2.drawContours(overlap_img, overlapped_contours, -1, 255, -1)

            # Distance transform
            distance = ndi.distance_transform_edt(overlap_img > 0)

            # Find local maxima
            coords = peak_local_max(
                distance, footprint=np.ones((5, 5)), labels=overlap_img > 0
            )

            if len(coords) == 0:
                return 0

            # Create markers
            mask_markers = np.zeros(distance.shape, dtype=bool)
            mask_markers[tuple(coords.T)] = True
            markers, _ = ndi.label(mask_markers)

            # Watershed segmentation
            labels = watershed(-distance, markers, mask=overlap_img > 0)

            # Count separated regions
            num_separated = len(np.unique(labels)) - 1  # Subtract background

            # Additional larvae = separated - original overlapped count
            return max(0, num_separated - len(overlapped_contours))

        except Exception as e:
            print(f"Warning: Watershed separation failed: {e}")
            return 0

    def create_visualization(self, image, mask, contours):
        """
        Create visualization with contours overlay

        Args:
            image: Original PIL Image
            mask: Binary mask
            contours: List of contours

        Returns:
            RGB image with visualization
        """
        # Resize original image to mask size
        image_resized = image.resize(self.img_size)
        image_arr = np.array(image_resized)

        # Convert mask to RGB
        mask_rgb = cv2.cvtColor((mask * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)

        # Overlay mask (green tint)
        overlay = image_arr.copy()
        overlay[mask > 0] = overlay[mask > 0] * 0.6 + np.array([0, 255, 0]) * 0.4

        # Draw contours
        cv2.drawContours(overlay, contours, -1, (255, 0, 0), 2, cv2.LINE_AA)

        return overlay.astype(np.uint8)

    def predict(self, image):
        """
        Complete prediction pipeline

        Args:
            image: PIL Image object

        Returns:
            Dictionary with results:
            {
                'mask': binary mask,
                'total_count': total larvae count,
                'individual_count': individual larvae,
                'overlapped_count': overlapped larvae,
                'partial_count': partial larvae,
                'artifacts_count': artifacts,
                'confidence': confidence score,
                'visualization': RGB visualization image
            }
        """
        # Segment
        mask = self.segment(image)

        # Count
        count_results = self.count_contours(mask)

        # Create visualization
        visualization = self.create_visualization(
            image, mask, count_results['contours']
        )

        # Calculate confidence (based on median area consistency)
        confidence = self._calculate_confidence(count_results)

        return {
            'mask': mask,
            'visualization': visualization,
            'confidence': confidence,
            **count_results
        }

    def _calculate_confidence(self, count_results):
        """
        Calculate confidence score based on counting results

        Args:
            count_results: Results from count_contours

        Returns:
            Confidence score (0-1)
        """
        total = count_results['total_count']
        artifacts = count_results['artifacts_count']

        if total == 0:
            return 0.0

        # Lower confidence if high artifact ratio
        artifact_ratio = artifacts / (total + artifacts)
        confidence = 1.0 - (artifact_ratio * 0.5)

        # Lower confidence if high overlap ratio
        overlapped = count_results['overlapped_count']
        overlap_ratio = overlapped / total if total > 0 else 0
        confidence *= (1.0 - overlap_ratio * 0.3)

        return max(0.0, min(1.0, confidence))
