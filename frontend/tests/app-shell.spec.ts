import { expect, test } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

test('renders the Vite React app and captures artifacts', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Get started' })).toBeVisible()
  await expect(page.getByRole('button', { name: /count is 0/i })).toBeVisible()

  const artifactsDir = path.join(process.cwd(), 'artifacts', 'app')
  await mkdir(artifactsDir, { recursive: true })

  await page.screenshot({
    path: path.join(artifactsDir, 'home.png'),
    fullPage: true,
  })

  await writeFile(
    path.join(artifactsDir, 'home.html'),
    await page.content(),
    'utf8',
  )
})
