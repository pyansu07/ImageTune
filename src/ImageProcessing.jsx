import React, { useState } from 'react';
import ImageContainer from './ImageContainer';
import './ImageProcessing.css';

const ImageProcessing = () => {
  const [file, setFile] = useState(null);
  const [enhancedImage, setEnhancedImage] = useState(null);
  const [denoisedImage, setDenoisedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('http://localhost:5000/api/process-image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Image processing failed');
      }

      const result = await response.json();
      setEnhancedImage(result.enhancedImage);
      setDenoisedImage(result.denoisedImage);
    } catch (error) {
      console.error('Error:', error);
      setError('An error occurred while processing the image. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="launch-container-p">
      <div className="launches-process">
        <h2 className="title-process">Image Processing</h2>
        <div className="form-container-process">
          <form onSubmit={handleSubmit} className="form-process">
            <input
              type="file"
              onChange={handleFileChange}
              accept="image/*"
              className="file-input-process"
            />
            <button
              type="submit"
              disabled={!file || isLoading}
              className="button1-process workButton-process"
            >
              {isLoading ? 'Processing...' : 'Process Image'}
            </button>
          </form>
          {error && <p className="error-message">{error}</p>}
        </div>

        {enhancedImage && denoisedImage && (
          <div className="image-comparison">
            <div className="image-container-wrapper">
              <h3 className="image-title-process">Enhanced Image</h3>
              <ImageContainer imageSrc={`data:image/png;base64,${enhancedImage}`} />
            </div>
            <div className="image-container-wrapper">
              <h3 className="image-title-process">Denoised Image</h3>
              <ImageContainer imageSrc={`data:image/png;base64,${denoisedImage}`} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageProcessing;