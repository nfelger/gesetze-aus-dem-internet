/** @type {import('gatsby).GatsbyConfig} */
module.exports = {
  siteMetadata: {
    title: `Gesetze aus dem Internet`,
    siteUrl: `https://nfelger.github.io/gesetze-aus-dem-internet/`,
  },
  plugins: [
    "gatsby-plugin-postcss",
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: `laws`,
        path: `${__dirname}/static/all_laws.json.gz`,
      }
    },
  ]
};
