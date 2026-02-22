/** @type {import('next').NextConfig} */
const nextConfig = {
    watchOptions: {
      ignored: ['**/backend/**', '**/node_modules/**'],
    },
  }
  
  module.exports = nextConfig