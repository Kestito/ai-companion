// Script to update logo and favicon files
const fs = require('fs');
const path = require('path');

// Paths
const publicDir = path.join(__dirname, '../public');
const appDir = path.join(__dirname, '../src/app');

console.log('Script started');
console.log('Public directory:', publicDir);
console.log('App directory:', appDir);

// Logo file copy from backup
try {
  console.log('Using EvelinaAIlogosmall.webp for all icons and logos');
  
  // Copy the EvelinaAIlogosmall.webp to favicon and icon files
  fs.copyFileSync(
    path.join(publicDir, 'EvelinaAIlogosmall.webp'),
    path.join(publicDir, 'favicon.ico')
  );
  console.log('Updated public/favicon.ico');
  
  fs.copyFileSync(
    path.join(publicDir, 'EvelinaAIlogosmall.webp'),
    path.join(publicDir, 'icon.ico')
  );
  console.log('Updated public/icon.ico');
  
  fs.copyFileSync(
    path.join(publicDir, 'EvelinaAIlogosmall.webp'),
    path.join(appDir, 'favicon.ico')
  );
  console.log('Updated app/favicon.ico');
  
  fs.copyFileSync(
    path.join(publicDir, 'EvelinaAIlogosmall.webp'),
    path.join(appDir, 'icon.ico')
  );
  console.log('Updated app/icon.ico');

  console.log('All icons updated successfully!');
} catch (error) {
  console.error('Error updating icons:', error.message);
} 