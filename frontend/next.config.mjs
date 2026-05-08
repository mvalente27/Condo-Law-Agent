/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === "production";
// Set NEXT_PUBLIC_BASE_PATH="/Condo-Law-Agent" for GitHub Pages project sites.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig = {
  reactStrictMode: true,
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
  basePath: isProd ? basePath : "",
  assetPrefix: isProd && basePath ? `${basePath}/` : undefined,
};

export default nextConfig;
