import * as React from "react"
import { useStaticQuery, graphql } from 'gatsby'

// styles
const pageStyles = {
  color: "#232129",
  padding: 96,
  fontFamily: "-apple-system, Roboto, sans-serif, serif",
}
const headingStyles = {
  marginTop: 0,
  marginBottom: 48,
  maxWidth: 320,
}
const paragraphStyles = {
  marginBottom: '1.4em',
}
const lastModifiedStyles = {
  color: "#8A6534",
  padding: 4,
  backgroundColor: "#FFF4DB",
  borderRadius: 4,
}
const listStyles = {
  marginBottom: 24,
  paddingLeft: 0,
}
const listItemStyles = {
  maxWidth: 560,
}
const linkStyle = {
  color: "#8954A8",
  fontWeight: "bold",
  fontSize: 16,
  verticalAlign: "5%",
}

// markup
const IndexPage = () => {
  const data = useStaticQuery(graphql`
    query MyQuery {
      laws: allFile(
        filter: {sourceInstanceName: {eq: "laws"}, relativeDirectory: {eq: "laws"}}
        sort: {fields: name}
      ) {
        nodes {
          relativePath
          name
        }
      }
      lastModified: allFile(filter: {name: {eq: "all_laws.json"}}) {
        nodes {
          birthTime(locale: "de", formatString: "dddd, [den] Do MMMM YYYY, hh:mm:ss [(]z[)]")
        }
      }
    }
  `)
  const laws = data.laws.nodes
  const lastModified = data.lastModified.nodes[0].birthTime

  return (
    <main style={pageStyles}>
      <title>Gesetze aus dem Internet</title>
      <h1 style={headingStyles}>Gesetze aus dem Internet</h1>
      <p style={paragraphStyles}>
        Zuletzt aktualisiert: <em style={lastModifiedStyles}>{lastModified}</em>
      </p>
      <p style={paragraphStyles}>
        Alle Gesetze als:
      </p>
      <ul style={listStyles}>
        <li style={listItemStyles}>
          <a style={linkStyle}
             href={`gadi/all_laws.json.gz`}
          >
            Große JSON-Datei (<code>all_laws.json.gz</code>)
          </a>
        </li>
        <li style={listItemStyles}>
          <a style={linkStyle}
             href={`gadi/all_laws.tar.gz`}
          >
            Tarball mit einzelnen JSON-Dateien je Gesetz (<code>all_laws.tar.gz</code>)
          </a>
        </li>
      </ul>
      <p style={paragraphStyles}>
        Oder direkt hier zu den einzelnen JSON-Dateien:
      </p>
      <ul style={listStyles}>
        {laws.map(law => (
          <li style={listItemStyles} key={law.relativePath}>
            <a
              style={linkStyle}
              href={`gadi/${law.relativePath}`}
            >
              {law.name}
            </a>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default IndexPage
