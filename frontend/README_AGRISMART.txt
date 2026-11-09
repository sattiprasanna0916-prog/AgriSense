AGRISMART FRONTEND UPDATE

This package contains the updated frontend src/ folder. It keeps the existing React routes, authentication flow, API calls, prediction/reliability/SHAP logic, historical insights, and AgriAssist chat integration while updating the brand and visual design.

INSTALL
1. Keep your existing project backup. Do not delete the backup.
2. Extract this ZIP.
3. Copy the included src folder into D:\CropRecommendationAI\frontend\ and replace the existing src folder when prompted.
4. Keep your existing package.json, package-lock.json, vite.config.*, node_modules, and backend files unchanged.
5. Open PowerShell:
   cd D:\CropRecommendationAI\frontend
   npm run build
6. If the build succeeds, start the backend in its usual terminal, then start the frontend:
   npm run dev
7. Open http://localhost:5173 and test login, crop recommendation, historical insights, AI assistant, and About.

IMPORTANT FUNCTIONAL NOTES
- The TabPFN model still receives exactly seven crop features: N, P, K, temperature, humidity, pH, and rainfall.
- State, district, and season remain in the separate Optional Context area. They are used for historical production context/ranking, not passed as extra TabPFN model features.
- No backend change is required for this visual redesign because the existing API contracts are preserved.
- The localStorage token key remains "agrisense_token" intentionally so existing signed-in sessions and backend authentication continue to work. It is an internal storage key, not a visible brand label.
- The screenshot's Weather Forecast, Soil Upload, and Crop Advisory pages were not added as fake links: the current frontend/backend source supplied does not include those working modules. They should only be added after implementing their real data/API functionality.
