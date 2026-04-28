export type ID = number;

export interface Banner {
  id: ID;
  photo?: string | null;
}

export interface CategoryEntity {
  id: ID;
  name_uz: string;
  name_ru: string;
  name_eng: string;
}

export interface CollectionEntity {
  id: ID;
  name_uz: string;
  name_ru: string;
  name_eng: string;
}

export interface ColorEntity {
  id: ID;
  name_uz: string;
  name_ru: string;
  name_eng: string;
}

export interface SizeEntity {
  id: ID;
  name: string;
}

export interface ProductItemEntity {
  id: ID;
  product_id: ID;
  color_id: ID;
  size_id: ID;
  total_count: number;
}

export interface ProductPhotoEntity {
  id: ID;
  product_id: ID;
  photo: string;
}

export interface ProductDetailEntity {
  id: ID;
  product_id: ID;
  name_uz: string;
  name_ru: string;
  name_eng: string;
}

export interface ProductEntity {
  id: ID;
  category_id: ID;
  collection_id: ID;
  name_uz: string;
  name_ru: string;
  name_eng: string;
  description_uz: string;
  description_ru: string;
  description_eng: string;
  is_active: boolean;
  price: number;
  item_ids: ID[];
  photo_ids: ID[];
  detail_ids: ID[];
}

export interface FrontendBootstrapNormalizedEntities {
  categories: Record<ID, CategoryEntity>;
  collections: Record<ID, CollectionEntity>;
  colors: Record<ID, ColorEntity>;
  sizes: Record<ID, SizeEntity>;
  products: Record<ID, ProductEntity>;
  product_items: Record<ID, ProductItemEntity>;
  product_photos: Record<ID, ProductPhotoEntity>;
  product_details: Record<ID, ProductDetailEntity>;
}

export interface FrontendBootstrapNormalizedResult {
  product_ids: ID[];
}

export interface FrontendBootstrapNormalizedResponse {
  ok: boolean;
  banners: Banner[];
  entities: FrontendBootstrapNormalizedEntities;
  result: FrontendBootstrapNormalizedResult;
}

// Optional helper shape for UI-ready resolved product cards.
export interface ResolvedProductCard {
  id: ID;
  name_uz: string;
  price: number;
  category?: CategoryEntity;
  collection?: CollectionEntity;
  items: Array<{
    id: ID;
    total_count: number;
    color?: ColorEntity;
    size?: SizeEntity;
  }>;
  photos: ProductPhotoEntity[];
  details: ProductDetailEntity[];
}

export function resolveProducts(
  payload: FrontendBootstrapNormalizedResponse,
): ResolvedProductCard[] {
  const { entities, result } = payload;

  return result.product_ids
    .map((productId) => entities.products[productId])
    .filter(Boolean)
    .map((p) => ({
      id: p.id,
      name_uz: p.name_uz,
      price: p.price,
      category: entities.categories[p.category_id],
      collection: entities.collections[p.collection_id],
      items: p.item_ids
        .map((id) => entities.product_items[id])
        .filter(Boolean)
        .map((it) => ({
          id: it.id,
          total_count: it.total_count,
          color: entities.colors[it.color_id],
          size: entities.sizes[it.size_id],
        })),
      photos: p.photo_ids.map((id) => entities.product_photos[id]).filter(Boolean),
      details: p.detail_ids.map((id) => entities.product_details[id]).filter(Boolean),
    }));
}
