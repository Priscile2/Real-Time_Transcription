# Use an official Node.js image
FROM node:18

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Build the Nuxt app
RUN npm run build

# Expose Nuxt default port
EXPOSE 3000

# Start Nuxt app in production mode
CMD ["npm", "run", "preview"]
WORKDIR /app
COPY live-transcription-web/package.json ./
COPY live-transcription-web/package-lock.json ./
