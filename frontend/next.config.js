/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NO_STANDALONE ? undefined : "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

module.exports = nextConfig;
