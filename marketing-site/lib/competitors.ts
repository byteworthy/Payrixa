import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

export function getCompetitorData(slug: string) {
  const filePath = path.join(
    process.cwd(),
    'content/competitors/data',
    `${slug}.json`
  );
  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents);
}

export async function getComparisonContent(slug: string) {
  const filePath = path.join(
    process.cwd(),
    'content/competitors',
    `${slug}.mdx`
  );
  const fileContents = fs.readFileSync(filePath, 'utf8');
  const { data, content } = matter(fileContents);

  return {
    ...data,
    body: content,
  };
}

export function getAllCompetitors() {
  const dataDir = path.join(process.cwd(), 'content/competitors/data');
  const files = fs.readdirSync(dataDir);

  return files
    .filter(file =>
      file.endsWith('.json') &&
      !file.includes('upstream') &&
      !file.includes('framework') &&
      !file.includes('types')
    )
    .map(file => file.replace('.json', ''));
}

export function getAllComparisonPages() {
  const contentDir = path.join(process.cwd(), 'content/competitors');
  const files = fs.readdirSync(contentDir);

  return files
    .filter(file => file.endsWith('.mdx') && file.startsWith('vs-'))
    .map(file => file.replace('.mdx', ''));
}

export function getAllAlternativePages() {
  const altDir = path.join(process.cwd(), 'content/competitors/alternatives');

  if (!fs.existsSync(altDir)) {
    return [];
  }

  const files = fs.readdirSync(altDir);

  return files
    .filter(file => file.endsWith('.mdx'))
    .map(file => file.replace('.mdx', ''));
}
