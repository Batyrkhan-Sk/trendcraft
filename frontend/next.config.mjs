/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Thumbnails come from platform CDNs; the set is open-ended so remote
  // patterns stay permissive and next/image is used only where we control size.
  images: { remotePatterns: [{ protocol: "https", hostname: "**" }] },
};
export default nextConfig;
