export const DEFAULT_IMAGE_PATH = '/assets/daylilies/placeholder.jpg';

export function getImageUrl(imageName: string): string {
    if (!imageName) return DEFAULT_IMAGE_PATH;
    return `/assets/daylilies/${imageName}`;
}