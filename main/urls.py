from django.urls import path
from . import views

urlpatterns = [
    # Test Firebase connection
    path('test/', views.test_firebase, name='test_firebase'),
    
    # ImgBB / Firebase 
    path("upload/", views.upload_image, name="upload_image"),
    path("show/", views.show_images, name="show_images"),

    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('properties/', views.buyorsell, name='buyorsell'),
    path('properties/submit/', views.submit_property, name='submit_property'),
    path('contact/', views.contact, name='contact'),

    # Custom Admin
    path('admin-portal/login/', views.admin_login_view, name='admin_login'),
    path('admin-portal/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-portal/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    # Admin – Gallery
    path('admin-portal/gallery/upload/', views.admin_upload_gallery, name='admin_upload_gallery'),
    path('admin-portal/gallery/delete/<str:pk>/', views.admin_delete_gallery, name='admin_delete_gallery'),

    # Admin – Categories
    path('admin-portal/categories/add/', views.admin_add_category, name='admin_add_category'),
    path('admin-portal/categories/delete/<str:pk>/', views.admin_delete_category, name='admin_delete_category'),

    # Admin – Listings
    path('admin-portal/listings/approve/<str:pk>/', views.admin_approve_listing, name='admin_approve_listing'),
    path('admin-portal/listings/reject/<str:pk>/', views.admin_reject_listing, name='admin_reject_listing'),
    path('admin-portal/listings/delete/<str:pk>/', views.admin_delete_listing, name='admin_delete_listing'),
]
