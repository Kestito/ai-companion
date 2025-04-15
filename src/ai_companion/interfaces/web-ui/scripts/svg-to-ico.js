// SVG to ICO conversion script
const fs = require('fs');
const path = require('path');
const svg2img = require('svg2img');
const Jimp = require('jimp');
const toIco = require('to-ico');

const svgPath = path.join(__dirname, '../public/logo.svg');
const icoOutputPath = path.join(__dirname, '../public/favicon.ico');
const appIcoOutputPath = path.join(__dirname, '../public/icon.ico');
const appLayoutIcoPath = path.join(__dirname, '../src/app/favicon.ico');
const appLayoutIconPath = path.join(__dirname, '../src/app/icon.ico');

// Read the SVG file
const svgContent = fs.readFileSync(svgPath, 'utf8');

// Convert SVG to PNG with svg2img
svg2img(svgContent, (error, buffer) => {
  if (error) {
    console.error('Error converting SVG to PNG:', error);
    return;
  }

  // Create temp PNG file
  const tempPngPath = path.join(__dirname, 'temp-icon.png');
  fs.writeFileSync(tempPngPath, buffer);

  // Process with Jimp to create different sizes
  Jimp.read(tempPngPath)
    .then(image => {
      return Promise.all([
        image.clone().resize(16, 16).getBufferAsync(Jimp.MIME_PNG),
        image.clone().resize(32, 32).getBufferAsync(Jimp.MIME_PNG),
        image.clone().resize(48, 48).getBufferAsync(Jimp.MIME_PNG),
        image.clone().resize(64, 64).getBufferAsync(Jimp.MIME_PNG),
        image.clone().resize(128, 128).getBufferAsync(Jimp.MIME_PNG)
      ]);
    })
    .then(images => {
      // Convert to ICO
      return toIco(images);
    })
    .then(icoBuffer => {
      // Save the ICO files
      fs.writeFileSync(icoOutputPath, icoBuffer);
      fs.writeFileSync(appIcoOutputPath, icoBuffer);
      
      // Copy to src/app directory
      fs.writeFileSync(appLayoutIcoPath, icoBuffer);
      fs.writeFileSync(appLayoutIconPath, icoBuffer);
      
      console.log('ICO files created successfully!');
      
      // Clean up temp file
      fs.unlinkSync(tempPngPath);
    })
    .catch(err => {
      console.error('Error in ICO conversion process:', err);
    });
}); 