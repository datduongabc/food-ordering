import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw/http'
import { describe, expect, it } from 'vitest'
import type { AdminProduct } from '@/features/admin/schemas'
import { admin, adminDish, adminUser, page } from '../support/adminFixtures'
import { apiError, mockApi, mockLayout, recordCalls } from '../support/api'
import { district1, mains, shakingBeef, starters } from '../support/fixtures'
import { renderApp } from '../support/render'
import { server } from '../support/server'

const hiddenDish: AdminProduct = {
  ...shakingBeef,
  created_at: '2026-10-01T03:00:00Z',
  deleted_at: '2026-10-20T03:00:00Z',
}

describe('admin dishes', () => {
  it('find dishes without typing accents and bring back hidden ones', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish, hiddenDish])
    const calls = recordCalls([
      'post',
      `/admin/products/${shakingBeef.id}/restore`,
      { ...hiddenDish, deleted_at: null },
    ])
    renderApp('/admin/products')

    expect(await screen.findByText('Gỏi cuốn tôm thịt')).toBeInTheDocument()
    expect(screen.queryByText('Bò lúc lắc')).not.toBeInTheDocument()
    expect(screen.getByText('1 kết quả')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Tìm món'), 'goi cuon')
    expect(screen.getByText('Gỏi cuốn tôm thịt')).toBeInTheDocument()
    await user.clear(screen.getByLabelText('Tìm món'))
    await user.type(screen.getByLabelText('Tìm món'), 'lau')
    expect(await screen.findByText('Không có kết quả phù hợp')).toBeInTheDocument()
    await user.clear(screen.getByLabelText('Tìm món'))

    await user.click(screen.getByLabelText('Hiện cả món đã ẩn'))
    const row = (await screen.findByText('Bò lúc lắc')).closest('tr')!
    expect(within(row).getByText('Đã ẩn')).toBeInTheDocument()
    await user.click(within(row).getByRole('button', { name: 'Bán lại Bò lúc lắc' }))

    expect(await screen.findByText('Đã đưa Bò lúc lắc trở lại thực đơn.')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
  })

  it('edit a dish, keeping its URL, and replace its photo', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters, mains])
    const calls = recordCalls([
      'patch',
      `/admin/products/${adminDish.id}`,
      { ...adminDish, price: 250_000 },
    ])
    const uploads: File[] = []
    server.use(
      http.put(`*/api/admin/products/${adminDish.id}/image`, async ({ request }) => {
        uploads.push((await request.formData()).get('image') as File)
        return HttpResponse.json(adminDish)
      }),
    )
    renderApp(`/admin/products/${adminDish.id}`)

    expect(
      await screen.findByRole('heading', { name: 'Sửa món: Gỏi cuốn tôm thịt' }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Tên tiếng Anh')).toHaveValue('Shrimp Spring Rolls')
    expect(screen.getByLabelText('Danh mục')).toHaveValue(String(starters.id))
    expect(screen.getByLabelText('DaTeNO - Quận 1')).toBeChecked()

    await user.clear(screen.getByLabelText('Giá (VND)'))
    await user.type(screen.getByLabelText('Giá (VND)'), '250 000')
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))
    expect(await screen.findByText('Đã lưu thay đổi.')).toBeInTheDocument()
    expect(calls[0]!.body).toMatchObject({
      slug: 'shrimp-spring-rolls',
      price: 250_000,
      location_ids: [district1.id],
    })

    expect(screen.getByRole('button', { name: 'Tải ảnh lên' })).toBeDisabled()
    const photo = new File(['webp'], 'goi-cuon.webp', { type: 'image/webp' })
    await user.upload(screen.getByLabelText('Chọn ảnh'), photo)
    await user.click(screen.getByRole('button', { name: 'Tải ảnh lên' }))
    expect(await screen.findByText('Đã cập nhật ảnh món.')).toBeInTheDocument()
    // jsdom drops the file name from multipart bodies; the bytes still arrive.
    expect(await uploads[0]!.text()).toBe('webp')
    expect(screen.getByRole('button', { name: 'Tải ảnh lên' })).toBeDisabled()
  })

  it('show why a photo was refused', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters])
    mockApi(
      'put',
      `/admin/products/${adminDish.id}/image`,
      apiError('image_too_large', { max_mb: 5 }),
      400,
    )
    renderApp(`/admin/products/${adminDish.id}`)

    await user.upload(
      await screen.findByLabelText('Chọn ảnh'),
      new File(['x'], 'big.jpg', { type: 'image/jpeg' }),
    )
    await user.click(screen.getByRole('button', { name: 'Tải ảnh lên' }))
    expect(await screen.findByText('Ảnh phải nhỏ hơn hoặc bằng 5 MB.')).toBeInTheDocument()
  })

  it('reject an impossible price, a bad URL and no branches', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters])
    renderApp(`/admin/products/${adminDish.id}`)

    await user.clear(await screen.findByLabelText('Giá (VND)'))
    await user.type(screen.getByLabelText('Giá (VND)'), '0')
    await user.clear(screen.getByLabelText('Đường dẫn (không bắt buộc)'))
    await user.type(screen.getByLabelText('Đường dẫn (không bắt buộc)'), 'Gỏi Cuốn')
    await user.click(screen.getByLabelText('DaTeNO - Quận 1'))
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))

    expect(
      await screen.findByText('Giá phải là số nguyên dương, tối đa 100.000.000.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Chỉ dùng chữ thường không dấu, số và dấu gạch ngang.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Chọn ít nhất một chi nhánh.')).toBeInTheDocument()
  })

  it('open the edit page of a new dish once it is saved', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/categories', [starters])
    const created: AdminProduct = {
      ...adminDish,
      id: 77,
      name: { vi: 'Bánh xèo', en: 'Sizzling Crepe' },
      slug: 'sizzling-crepe',
    }
    let products = [adminDish]
    server.use(
      http.get('*/api/admin/products', () => HttpResponse.json(products)),
      http.post('*/api/admin/products', () => {
        products = [...products, created]
        return HttpResponse.json(created, { status: 201 })
      }),
    )
    const { router } = renderApp('/admin/products/new')

    expect(await screen.findByText('Có thể thêm ảnh sau khi lưu món.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Tên tiếng Việt'), 'Bánh xèo')
    await user.type(screen.getByLabelText('Tên tiếng Anh'), 'Sizzling Crepe')
    await user.type(screen.getByLabelText('Mô tả tiếng Việt'), 'Giòn rụm.')
    await user.type(screen.getByLabelText('Mô tả tiếng Anh'), 'Crispy.')
    await user.type(screen.getByLabelText('Giá (VND)'), '95000')
    await user.selectOptions(screen.getByLabelText('Danh mục'), 'Khai vị')
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }))

    expect(await screen.findByText('Đã thêm Bánh xèo.')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Sửa món: Bánh xèo' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/admin/products/77')
  })

  it('treat unknown and malformed dish addresses as missing pages', async () => {
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters])
    renderApp('/admin/products/999')
    expect(await screen.findByText('Không tìm thấy trang')).toBeInTheDocument()
  })

  it('go back to the list without saving', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/products', [adminDish])
    mockApi('get', '/categories', [starters])
    const { router } = renderApp('/admin/products/0')

    expect(await screen.findByText('Không tìm thấy trang')).toBeInTheDocument()
    await router.navigate(`/admin/products/${adminDish.id}`)
    await user.click(await screen.findByRole('button', { name: 'Hủy' }))
    expect(router.state.location.pathname).toBe('/admin/products')
  })
})

describe('admin users', () => {
  it('search accounts, include deactivated ones and restore one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    const queries: URLSearchParams[] = []
    server.use(
      http.get('*/api/admin/users', ({ request }) => {
        const query = new URL(request.url).searchParams
        queries.push(query)
        return HttpResponse.json(
          page(
            query.get('include_deactivated') === 'true'
              ? [adminUser({ deleted_at: '2026-10-20T03:00:00Z', is_email_verified: false })]
              : [adminUser()],
            { total: 21, total_pages: 2 },
          ),
        )
      }),
    )
    const calls = recordCalls(['post', '/admin/users/7/restore', adminUser()])
    renderApp('/admin/users')

    expect(await screen.findByText('Nguyen Van A')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Tìm theo tên, email, số điện thoại'), 'nguyen')
    await expect.poll(() => queries.at(-1)?.get('q')).toBe('nguyen')

    await user.click(screen.getByRole('button', { name: 'Trang 2' }))
    await expect.poll(() => queries.at(-1)?.get('page')).toBe('2')

    await user.click(screen.getByLabelText('Hiện cả tài khoản đã vô hiệu hóa'))
    const row = (await screen.findByText('Đã vô hiệu hóa')).closest('tr')!
    expect(within(row).getByText('Chưa xác thực')).toBeInTheDocument()
    await user.click(within(row).getByRole('button', { name: 'Khôi phục Nguyen Van A' }))
    expect(await screen.findByText('Đã khôi phục Nguyen Van A.')).toBeInTheDocument()
    expect(calls).toHaveLength(1)
  })

  it('create an admin, requiring a password and showing a taken email under its field', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/users', page([adminUser()]))
    const calls = recordCalls(['post', '/admin/users', apiError('email_or_phone_taken'), 409])
    renderApp('/admin/users')

    await user.click(await screen.findByRole('button', { name: '+ Thêm người dùng' }))
    const form = screen.getByRole('form', { name: 'Thêm người dùng' })
    await user.click(within(form).getByRole('button', { name: 'Lưu thay đổi' }))
    expect(within(form).getByText('Mật khẩu cần tối thiểu 8 ký tự.')).toBeInTheDocument()
    expect(calls).toHaveLength(0)

    await user.type(within(form).getByLabelText('Họ và tên'), 'Pham Thu')
    await user.type(within(form).getByLabelText('Email'), 'Thu@Example.com')
    await user.type(within(form).getByLabelText('Số điện thoại'), '0912 345 678')
    await user.selectOptions(within(form).getByLabelText('Vai trò'), 'Quản trị viên')
    await user.type(within(form).getByLabelText('Mật khẩu'), 'mat-khau-123')
    await user.click(within(form).getByLabelText('Email đã được xác thực'))
    await user.click(within(form).getByRole('button', { name: 'Lưu thay đổi' }))

    expect(
      await within(form).findByText('Email hoặc số điện thoại đã được tài khoản khác sử dụng.'),
    ).toBeInTheDocument()
    expect(calls[0]!.body).toEqual({
      name: 'Pham Thu',
      email: 'thu@example.com',
      phone: '0912345678',
      role: 'ADMIN',
      email_verified: true,
      password: 'mat-khau-123',
    })

    await user.click(within(form).getByRole('button', { name: 'Hủy' }))
    expect(screen.queryByRole('form', { name: 'Thêm người dùng' })).not.toBeInTheDocument()
  })

  it('set a new password for a customer and close the form when saved', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/users', page([adminUser()]))
    const calls = recordCalls(['patch', '/admin/users/7', adminUser()])
    renderApp('/admin/users')

    await user.click(await screen.findByRole('button', { name: 'Sửa Nguyen Van A' }))
    const form = screen.getByRole('form', { name: 'Sửa người dùng: Nguyen Van A' })
    await user.type(
      within(form).getByLabelText('Mật khẩu mới (để trống nếu không đổi)'),
      'mat-khau-moi-1',
    )
    await user.click(within(form).getByRole('button', { name: 'Lưu thay đổi' }))

    expect(await screen.findByText('Đã lưu thay đổi.')).toBeInTheDocument()
    expect(calls[0]!.body).toMatchObject({ password: 'mat-khau-moi-1', role: 'CUSTOMER' })
    expect(screen.queryByRole('form')).not.toBeInTheDocument()
  })

  it('explain a refused deactivation and allow backing out of one', async () => {
    const user = userEvent.setup()
    mockLayout({ signedIn: admin })
    mockApi('get', '/admin/users', page([adminUser()]))
    recordCalls(['post', '/admin/users/7/deactivate', apiError('user_not_found'), 404])
    renderApp('/admin/users')

    const row = (await screen.findByText('Nguyen Van A')).closest('tr')!
    await user.click(within(row).getByRole('button', { name: 'Vô hiệu hóa Nguyen Van A' }))
    await user.click(within(row).getByRole('button', { name: 'Hủy' }))
    expect(within(row).queryByRole('alertdialog')).not.toBeInTheDocument()

    await user.click(within(row).getByRole('button', { name: 'Vô hiệu hóa Nguyen Van A' }))
    await user.click(within(row).getByRole('button', { name: 'Vô hiệu hóa' }))
    expect(await screen.findByText('Không tìm thấy người dùng.')).toBeInTheDocument()
  })
})
