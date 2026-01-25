/**
 * Clipboard Utility
 * Provides methods to copy text or DOM element content to clipboard
 * with robust fallbacks for different browser environments.
 */

/**
 * Copies text to clipboard using the modern API or fallback.
 * @param text The string to copy
 * @returns Promise<boolean> indicating success
 */
export async function copyText(text: string): Promise<boolean> {
  if (!text) return false

  // Try Modern Async API
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch (err) {
    console.warn('Clipboard API failed, falling back to execCommand', err)
  }

  // Fallback: Create hidden textarea
  const textArea = document.createElement("textarea")
  textArea.value = text
  
  // Ensure it's not visible but part of DOM
  textArea.style.position = 'fixed'
  textArea.style.left = '-9999px'
  textArea.style.top = '0'
  document.body.appendChild(textArea)
  
  textArea.focus()
  textArea.select()
  
  try {
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch (err) {
    console.error('Fallback copy failed', err)
    document.body.removeChild(textArea)
    return false
  }
}

/**
 * Copies text content from a DOM element matching the selector.
 * Useful for preserving formatting or copying large text blocks rendered in <pre> tags.
 * 
 * @param selector CSS selector to find the element
 * @returns boolean indicating success
 */
export function copyElementContent(selector: string): boolean {
  // Try to find the element
  const element = document.querySelector(selector)
  if (!element) return false

  // Create selection range
  const range = document.createRange()
  range.selectNodeContents(element)
  
  const selection = window.getSelection()
  if (!selection) return false
  
  // Apply selection
  selection.removeAllRanges()
  selection.addRange(range)

  try {
    // Execute copy
    const successful = document.execCommand('copy')
    return successful
  } catch (err) {
    console.error('Copy element content failed', err)
    return false
  } finally {
    // Clean up selection
    selection.removeAllRanges()
  }
}
