# Building Admin UIs with FastAPI Admin SDK + shadcn/ui + Next.js

This guide demonstrates how to build a dynamic admin interface using FastAPI Admin SDK as the backend and shadcn/ui components with Next.js for the frontend.

## Overview

The FastAPI Admin SDK provides a manifest API (`GET /admin/manifest`) that returns all registered resources with their schemas, permissions, and configurations. This makes it perfect for building dynamic admin UIs that can automatically discover and render forms, tables, and actions based on the backend configuration.

## Architecture

```text
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js App   │  ────>  │  FastAPI Admin   │  ────>  │   Database      │
│   (shadcn/ui)   │         │      SDK         │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
       │                              │
       │                              │
       └────── Manifest API ──────────┘
```

## Setup

### 1. Backend (FastAPI)

First, set up your FastAPI backend with the admin SDK:

```python
from fastapi import FastAPI
from fastapi_admin_sdk import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/admin")
```

### 2. Frontend (Next.js + shadcn/ui)

Initialize a Next.js project and install shadcn/ui:

```bash
npx create-next-app@latest admin-ui --typescript --tailwind --app
cd admin-ui
npx shadcn-ui@latest init
```

Install shadcn/ui components you'll need:

```bash
npx shadcn-ui@latest add button card table input label select dialog form
```

## Implementation

### 1. Type Definitions

Create type definitions based on the manifest API response:

```typescript
// types/admin.ts
export interface ResourceManifest {
  name: string;
  verbose_name: string;
  actions: string[];
  list_config: {
    display_fields: string[];
    filter_fields: string[];
    search_fields: string[];
    ordering: string[];
  };
  create_schema: JSONSchema;
  update_schema: JSONSchema;
}

export interface ManifestResponse {
  resources: ResourceManifest[];
}

export interface JSONSchema {
  type: string;
  properties?: Record<string, FieldSchema>;
  required?: string[];
}

export interface FieldSchema {
  type: string;
  format?: string;
  "x-field-type"?: string;
  maxLength?: number;
  minLength?: number;
  enum?: any[];
  [key: string]: any;
}
```

### 2. API Client

Create a client to interact with your FastAPI backend:

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchManifest(): Promise<ManifestResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/manifest`, {
    credentials: 'include', // Include cookies for auth
  });
  if (!response.ok) throw new Error('Failed to fetch manifest');
  return response.json();
}

export async function listResource(
  resourceName: string,
  params: {
    limit?: number;
    offset?: number;
    filters?: string;
    ordering?: string;
  } = {}
): Promise<any> {
  const queryParams = new URLSearchParams();
  if (params.limit) queryParams.set('limit', params.limit.toString());
  if (params.offset) queryParams.set('offset', params.offset.toString());
  if (params.filters) queryParams.set('filters', params.filters);
  if (params.ordering) queryParams.set('ordering', params.ordering);

  const response = await fetch(
    `${API_BASE_URL}/admin/${resourceName}/list?${queryParams}`,
    { credentials: 'include' }
  );
  if (!response.ok) throw new Error('Failed to list resource');
  return response.json();
}

export async function createResource(
  resourceName: string,
  data: Record<string, any>
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/admin/${resourceName}/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create resource');
  }
  return response.json();
}

export async function updateResource(
  resourceName: string,
  lookup: string,
  data: Record<string, any>
): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/admin/${resourceName}/${lookup}/update`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update resource');
  }
  return response.json();
}

export async function deleteResource(
  resourceName: string,
  lookup: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/admin/${resourceName}/${lookup}/delete`,
    {
      method: 'DELETE',
      credentials: 'include',
    }
  );
  if (!response.ok) throw new Error('Failed to delete resource');
}

export async function retrieveResource(
  resourceName: string,
  lookup: string
): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/admin/${resourceName}/${lookup}/retrieve`,
    { credentials: 'include' }
  );
  if (!response.ok) throw new Error('Failed to retrieve resource');
  return response.json();
}
```

### 3. Dynamic Form Component

Create a form component that renders based on JSON Schema:

```typescript
// components/DynamicForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FieldSchema, JSONSchema } from '@/types/admin';

interface DynamicFormProps {
  schema: JSONSchema;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  defaultValues?: Record<string, any>;
  submitLabel?: string;
}

// Convert JSON Schema to Zod schema
function jsonSchemaToZod(schema: JSONSchema): z.ZodObject<any> {
  const shape: Record<string, z.ZodTypeAny> = {};

  if (!schema.properties) {
    return z.object({});
  }

  for (const [key, fieldSchema] of Object.entries(schema.properties)) {
    const isRequired = schema.required?.includes(key) ?? false;
    let zodType: z.ZodTypeAny;

    switch (fieldSchema.type) {
      case 'string':
        if (fieldSchema.format === 'email') {
          zodType = z.string().email();
        } else {
          zodType = z.string();
        }
        if (fieldSchema.minLength) {
          zodType = zodType.min(fieldSchema.minLength);
        }
        if (fieldSchema.maxLength) {
          zodType = zodType.max(fieldSchema.maxLength);
        }
        break;
      case 'integer':
      case 'number':
        zodType = z.number();
        break;
      case 'boolean':
        zodType = z.boolean();
        break;
      default:
        zodType = z.any();
    }

    shape[key] = isRequired ? zodType : zodType.optional();
  }

  return z.object(shape);
}

// Render form field based on schema
function renderField(
  name: string,
  fieldSchema: FieldSchema,
  register: any,
  errors: any,
  control?: any
) {
  const fieldType = fieldSchema['x-field-type'] || fieldSchema.type;

  switch (fieldType) {
    case 'email':
      return (
        <div key={name} className="space-y-2">
          <Label htmlFor={name}>{name}</Label>
          <Input
            id={name}
            type="email"
            {...register(name)}
            className={errors[name] ? 'border-red-500' : ''}
          />
          {errors[name] && (
            <p className="text-sm text-red-500">{errors[name].message}</p>
          )}
        </div>
      );

    case 'char':
    case 'string':
      return (
        <div key={name} className="space-y-2">
          <Label htmlFor={name}>{name}</Label>
          <Input
            id={name}
            {...register(name)}
            maxLength={fieldSchema.maxLength}
            className={errors[name] ? 'border-red-500' : ''}
          />
          {errors[name] && (
            <p className="text-sm text-red-500">{errors[name].message}</p>
          )}
        </div>
      );

    case 'select':
      return (
        <div key={name} className="space-y-2">
          <Label htmlFor={name}>{name}</Label>
          <Select name={name}>
            <SelectTrigger>
              <SelectValue placeholder={`Select ${name}`} />
            </SelectTrigger>
            <SelectContent>
              {fieldSchema.enum?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors[name] && (
            <p className="text-sm text-red-500">{errors[name].message}</p>
          )}
        </div>
      );

    default:
      return (
        <div key={name} className="space-y-2">
          <Label htmlFor={name}>{name}</Label>
          <Input
            id={name}
            {...register(name)}
            className={errors[name] ? 'border-red-500' : ''}
          />
          {errors[name] && (
            <p className="text-sm text-red-500">{errors[name].message}</p>
          )}
        </div>
      );
  }
}

export function DynamicForm({
  schema,
  onSubmit,
  defaultValues = {},
  submitLabel = 'Submit',
}: DynamicFormProps) {
  const zodSchema = jsonSchemaToZod(schema);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(zodSchema),
    defaultValues,
  });

  const fields = schema.properties ? Object.entries(schema.properties) : [];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {fields.map(([name, fieldSchema]) =>
        renderField(name, fieldSchema, register, errors)
      )}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : submitLabel}
      </Button>
    </form>
  );
}
```

### 4. Resource List Component

Create a component to display resource lists:

```typescript
// components/ResourceList.tsx
'use client';

import { useEffect, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { listResource, deleteResource } from '@/lib/api';
import { ResourceManifest } from '@/types/admin';
import { DynamicForm } from './DynamicForm';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { createResource, updateResource, retrieveResource } from '@/lib/api';

interface ResourceListProps {
  resource: ResourceManifest;
  lookupField: string;
}

export function ResourceList({ resource, lookupField }: ResourceListProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const filters = search
        ? JSON.stringify({
            [resource.list_config.search_fields[0]]: search,
          })
        : undefined;
      const result = await listResource(resource.name, {
        limit: 10,
        offset,
        filters,
      });
      setData(result);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [offset, search]);

  const handleCreate = async (formData: Record<string, any>) => {
    await createResource(resource.name, formData);
    setCreateOpen(false);
    loadData();
  };

  const handleUpdate = async (formData: Record<string, any>) => {
    if (editingItem) {
      await updateResource(resource.name, editingItem[lookupField], formData);
      setEditOpen(false);
      setEditingItem(null);
      loadData();
    }
  };

  const handleDelete = async (item: any) => {
    if (confirm('Are you sure you want to delete this item?')) {
      await deleteResource(resource.name, item[lookupField]);
      loadData();
    }
  };

  const handleEdit = async (item: any) => {
    const fullItem = await retrieveResource(resource.name, item[lookupField]);
    setEditingItem(fullItem);
    setEditOpen(true);
  };

  const displayFields = resource.list_config.display_fields || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">{resource.verbose_name}</h2>
        {resource.actions.includes('create') && (
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button>Create New</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create {resource.verbose_name}</DialogTitle>
              </DialogHeader>
              <DynamicForm
                schema={resource.create_schema}
                onSubmit={handleCreate}
                submitLabel="Create"
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      {resource.list_config.search_fields.length > 0 && (
        <Input
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      )}

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                {displayFields.map((field) => (
                  <TableHead key={field}>{field}</TableHead>
                ))}
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item) => (
                <TableRow key={item[lookupField]}>
                  {displayFields.map((field) => (
                    <TableCell key={field}>{item[field]}</TableCell>
                  ))}
                  <TableCell>
                    <div className="flex gap-2">
                      {resource.actions.includes('update') && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(item)}
                        >
                          Edit
                        </Button>
                      )}
                      {resource.actions.includes('delete') && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(item)}
                        >
                          Delete
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={() => setOffset(Math.max(0, offset - 10))}
              disabled={offset === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              onClick={() => setOffset(offset + 10)}
              disabled={data.length < 10}
            >
              Next
            </Button>
          </div>
        </>
      )}

      {editOpen && editingItem && (
        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit {resource.verbose_name}</DialogTitle>
            </DialogHeader>
            <DynamicForm
              schema={resource.update_schema}
              onSubmit={handleUpdate}
              defaultValues={editingItem}
              submitLabel="Update"
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
```

### 5. Main Admin Page

Create the main admin page that loads the manifest and renders resources:

```typescript
// app/admin/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { fetchManifest } from '@/lib/api';
import { ResourceManifest } from '@/types/admin';
import { ResourceList } from '@/components/ResourceList';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function AdminPage() {
  const [resources, setResources] = useState<ResourceManifest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);

  useEffect(() => {
    async function loadManifest() {
      try {
        const manifest = await fetchManifest();
        setResources(manifest.resources);
        if (manifest.resources.length > 0) {
          setSelectedResource(manifest.resources[0].name);
        }
      } catch (error) {
        console.error('Failed to load manifest:', error);
      } finally {
        setLoading(false);
      }
    }
    loadManifest();
  }, []);

  if (loading) {
    return <div className="p-8">Loading admin...</div>;
  }

  const currentResource = resources.find((r) => r.name === selectedResource);

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 border-r p-4">
        <h1 className="text-xl font-bold mb-4">Admin</h1>
        <nav className="space-y-2">
          {resources.map((resource) => (
            <button
              key={resource.name}
              onClick={() => setSelectedResource(resource.name)}
              className={`w-full text-left p-2 rounded ${
                selectedResource === resource.name
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              {resource.verbose_name}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-auto">
        {currentResource ? (
          <ResourceList
            resource={currentResource}
            lookupField="id" // Adjust based on your resource configuration
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Select a resource</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Choose a resource from the sidebar to get started.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
```

## Additional Features

### Authentication

Add authentication to your API calls:

```typescript
// lib/api.ts
async function authenticatedFetch(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token'); // or use cookies
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}
```

### Error Handling

Add a global error handler:

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong.</div>;
    }
    return this.props.children;
  }
}
```

### Advanced Filtering

Enhance the filtering UI based on `filter_fields`:

```typescript
// components/FilterPanel.tsx
'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface FilterPanelProps {
  filterFields: string[];
  onApply: (filters: Record<string, any>) => void;
}

export function FilterPanel({ filterFields, onApply }: FilterPanelProps) {
  const [filters, setFilters] = useState<Record<string, string>>({});

  return (
    <div className="space-y-4 p-4 border rounded">
      <h3 className="font-semibold">Filters</h3>
      {filterFields.map((field) => (
        <div key={field}>
          <Label htmlFor={field}>{field}</Label>
          <Input
            id={field}
            value={filters[field] || ''}
            onChange={(e) =>
              setFilters({ ...filters, [field]: e.target.value })
            }
          />
        </div>
      ))}
      <Button onClick={() => onApply(filters)}>Apply Filters</Button>
    </div>
  );
}
```

## Benefits

1. **Zero Configuration**: The UI automatically adapts to your backend schema
2. **Type Safety**: TypeScript types ensure consistency
3. **Permission-Aware**: Only shows resources and actions the user can access
4. **Maintainable**: Changes to backend models automatically reflect in the UI
5. **Modern UI**: Uses shadcn/ui components for a polished, accessible interface

## Next Steps

- Add real-time updates with WebSockets
- Implement advanced filtering and sorting UI
- Add bulk actions for multiple resources
- Create custom field renderers for complex types
- Add export functionality (CSV, JSON)
- Implement audit logging and history tracking
