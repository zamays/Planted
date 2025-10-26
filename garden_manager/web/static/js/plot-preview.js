// Plot Preview - Update dimensions preview in real-time

document.addEventListener('DOMContentLoaded', function() {
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    const previewWidth = document.getElementById('preview-width');
    const previewHeight = document.getElementById('preview-height');
    const previewTotal = document.getElementById('preview-total');
    
    if (!widthInput || !heightInput || !previewWidth || !previewHeight || !previewTotal) {
        return; // Elements not found, exit gracefully
    }
    
    function updatePreview() {
        const width = parseInt(widthInput.value) || 4;
        const height = parseInt(heightInput.value) || 4;
        const total = width * height;
        
        previewWidth.textContent = width;
        previewHeight.textContent = height;
        previewTotal.textContent = total;
    }
    
    widthInput.addEventListener('input', updatePreview);
    heightInput.addEventListener('input', updatePreview);
});
