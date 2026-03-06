from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from functools import wraps
from django.contrib import messages
import sys
import os
# Ensure project root is accessible for importing firebase_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from firebase_config import db

# All application data has been migrated to Firebase Firestore.
# Local models are no longer used.
import requests
import base64
from datetime import datetime
import uuid
import re


# ─── Helpers ─────────────────────────────────────────────────────

# ─── Auth Decorator ──────────────────────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        admin_user = request.get_signed_cookie('admin_session', default=None)
        if not admin_user:
            messages.error(request, "Please login as admin to access this page.")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Load ImgBB key from environment
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "f4d21e33dfe671434b7306e2a1abd8e5")

def upload_to_imgbb(image_file):
    """Helper to upload a file to ImgBB and return the URL and delete URL."""
    try:
        image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        payload = {
            "key": IMGBB_API_KEY,
            "image": image_b64,
        }
        response = requests.post("https://api.imgbb.com/1/upload", data=payload)
        if response.status_code == 200:
            data = response.json().get('data', {})
            return data.get('url'), data.get('delete_url')
    except Exception as e:
        print(f"ImgBB Upload Error: {e}")
    return None, None

def delete_from_imgbb(delete_url):
    """Attempt to delete an image using its ImgBB delete_url."""
    if not delete_url: return
    try:
        s = requests.Session()
        res = s.get(delete_url)
        match = re.search(r'name="auth_token"\s+value="([^"]+)"', res.text)
        if match:
            auth_token = match.group(1)
            s.post(delete_url, data={'auth_token': auth_token, 'action': 'delete'})
    except Exception as e:
        print(f"ImgBB Delete Error for {delete_url}: {e}")


# ─── Public Views ─────────────────────────────────────────────────

def home(request):
    return render(request, 'main/home.html')


def about(request):
    return render(request, 'main/about.html')


def gallery(request):
    images = []
    docs = db.collection("images").stream()
    for doc in docs:
        data = doc.to_dict()
        images.append({
            'title': data.get('title', ''),
            'image': {'url': data.get('url', '')}
        })
    return render(request, 'main/gallery.html', {'images': images})


def buyorsell(request):
    # Fetch approved listings from Firestore
    # We remove order_by here to avoid the need for a composite index in Firestore
    listings_ref = db.collection("listings")
    query = listings_ref.where("status", "==", "approved")
    
    try:
        docs = query.stream()
        all_docs = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            all_docs.append(d)
            
        # Sort in Python by submitted_at (descending)
        all_docs.sort(key=lambda x: x.get('submitted_at').isoformat() if hasattr(x.get('submitted_at'), 'isoformat') else str(x.get('submitted_at') or ''), reverse=True)
        docs_to_process = all_docs
    except Exception as e:
        print(f"Firestore Query Error: {e}")
        docs_to_process = []

    grouped = {}
    for listing in docs_to_process:
        # id is already in the dictionary from the code above
        category_name = listing.get('property_type', 'Others').upper()
        
        if category_name not in grouped:
            grouped[category_name] = []
        grouped[category_name].append(listing)

    # Sort categories alphabetically for consistent UI
    sorted_grouped = sorted(grouped.items())

    return render(request, 'main/buyorsell.html', {
        'grouped_listings': sorted_grouped,
    })


def submit_property(request):
    if request.method == 'POST':
        owner_name = request.POST.get('owner_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        location = request.POST.get('location', '').strip()
        area = request.POST.get('area', '').strip()
        property_type = request.POST.get('property_type', '').strip()
        expected_price = request.POST.get('expected_price', '').strip()
        details = request.POST.get('details', '').strip()
        images = request.FILES.getlist('images')

        listing_type = request.POST.get('listing_type', 'offer')
        
        if owner_name and phone and property_type:
            try:
                # 1. Upload images to ImgBB
                img_urls = []
                delete_urls = []
                for img in images:
                    url, d_url = upload_to_imgbb(img)
                    if url:
                        img_urls.append(url)
                    if d_url:
                        delete_urls.append(d_url)
                
                # 2. Prepare Firestore data
                property_code = f"RBK-{uuid.uuid4().hex[:6].upper()}"
                listing_data = {
                    "property_code": property_code,
                    "owner_name": owner_name,
                    "phone": phone,
                    "location": location,
                    "area": area,
                    "property_type": property_type,
                    "expected_price": expected_price,
                    "details": details,
                    "listing_type": listing_type,
                    "status": "pending",
                    "submitted_at": datetime.now(),
                    "image_urls": img_urls,
                    "delete_urls": delete_urls
                }
                
                # 3. Save to Firestore
                db.collection("listings").add(listing_data)
                
                if listing_type == 'request':
                    messages.success(request, "Your request has been submitted successfully! We will contact you soon.")
                else:
                    success_msg = "Your property has been listed! It will appear on the site once approved."
                    if not img_urls and images:
                        success_msg += " (Note: Images failed to upload)"
                    messages.success(request, success_msg)
                    
            except Exception as e:
                messages.error(request, f"Something went wrong: {e}")
        else:
            messages.error(request, "Please fill in all required fields (*).")

    return redirect('buyorsell')


def contact(request):
    return render(request, 'main/contact.html')


# ─── Admin Auth Views ─────────────────────────────────────────────

def admin_login_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        # Check against Firestore admins collection
        # admins collection should have docs with 'username' and 'password' fields
        admin_docs = db.collection("admins").where("username", "==", user_name).limit(1).stream()
        admin_found = None
        for doc in admin_docs:
            admin_found = doc.to_dict()
            break
            
        if admin_found and admin_found.get('password') == pass_word:
            response = redirect('admin_dashboard')
            # Set a signed cookie to maintain "session"
            response.set_signed_cookie('admin_session', user_name, max_age=86400) # 1 day
            messages.success(request, f"Welcome back, {user_name}!")
            return response
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'main/admin_login.html')


def admin_logout_view(request):
    response = redirect('admin_login')
    response.delete_cookie('admin_session')
    messages.info(request, "You have been logged out.")
    return response


# ─── Admin Dashboard ──────────────────────────────────────────────

@admin_required
def admin_dashboard_view(request):
    admin_user = request.get_signed_cookie('admin_session', default="Admin")
    # 1. Gallery Images from Firebase
    gallery_images = []
    gallery_docs = db.collection("images").stream()
    for doc in gallery_docs:
        data = doc.to_dict()
        gallery_images.append({
            'pk': doc.id,
            'title': data.get('title', ''),
            'image': {'url': data.get('url', '')},
            'uploaded_at': data.get('uploaded_at')
        })
    gallery_images.sort(key=lambda x: str(x['uploaded_at'] or ''), reverse=True)

    # 2. Categories from Firestore
    categories = []
    category_docs = db.collection("categories").stream()
    for doc in category_docs:
        data = doc.to_dict()
        data['pk'] = doc.id
        categories.append(data)
    categories.sort(key=lambda x: x.get('name', ''))

    # 3. Property Listings from Firestore
    all_listings = []
    try:
        listing_docs = db.collection("listings").stream()
        for doc in listing_docs:
            data = doc.to_dict()
            data['id'] = doc.id
            all_listings.append(data)
        
        # Sort in Python by submitted_at (descending)
        all_listings.sort(key=lambda x: x.get('submitted_at').isoformat() if hasattr(x.get('submitted_at'), 'isoformat') else str(x.get('submitted_at') or ''), reverse=True)
    except Exception as e:
        print(f"Admin Dashboard Listing Error: {e}")
        all_listings = []
    
    pending_count = sum(1 for l in all_listings if l.get('status') == 'pending' and l.get('listing_type') == 'offer')
    offers = [l for l in all_listings if l.get('listing_type') == 'offer']
    requests_list = [l for l in all_listings if l.get('listing_type') == 'request']

    return render(request, 'main/admin_dashboard.html', {
        'gallery_images': gallery_images,
        'offers': offers,
        'requests': requests_list,
        'categories': categories,
        'gallery_count': len(gallery_images),
        'offer_count': len(offers),
        'request_count': len(requests_list),
        'pending_offer_count': pending_count,
        'admin_user': admin_user,
    })


# ─── Admin Gallery ────────────────────────────────────────────────

@admin_required
def admin_upload_gallery(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        image = request.FILES.get('image')
        if image:
            img_url, d_url = upload_to_imgbb(image)
            if img_url:
                db.collection("images").add({
                    "title": title,
                    "url": img_url,
                    "delete_url": d_url,
                    "uploaded_at": datetime.now()
                })
    return redirect('admin_dashboard')


@admin_required
def admin_delete_gallery(request, pk):
    if request.method == 'POST':
        doc_ref = db.collection("images").document(str(pk))
        doc = doc_ref.get()
        if doc.exists:
            img_data = doc.to_dict()
            if img_data.get('delete_url'):
                delete_from_imgbb(img_data['delete_url'])
        doc_ref.delete()
    return redirect('admin_dashboard')


# ─── Admin Categories ─────────────────────────────────────────────

@admin_required
def admin_add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            db.collection("categories").add({"name": name})
    return redirect('admin_dashboard')


@admin_required
def admin_delete_category(request, pk):
    if request.method == 'POST':
        db.collection("categories").document(str(pk)).delete()
    return redirect('admin_dashboard')


# ─── Admin Listing Actions ────────────────────────────────────────

@admin_required
def admin_approve_listing(request, pk):
    if request.method == 'POST':
        db.collection("listings").document(pk).update({"status": "approved"})
    return redirect('admin_dashboard')


@admin_required
def admin_reject_listing(request, pk):
    if request.method == 'POST':
        doc_ref = db.collection("listings").document(pk)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            urls = data.get('delete_urls', [])
            for d_url in urls:
                delete_from_imgbb(d_url)
        doc_ref.delete()
    return redirect('admin_dashboard')


@admin_required
def admin_delete_listing(request, pk):
    if request.method == 'POST':
        doc_ref = db.collection("listings").document(pk)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            urls = data.get('delete_urls', [])
            for d_url in urls:
                delete_from_imgbb(d_url)
        doc_ref.delete()
    
    next_url = request.META.get('HTTP_REFERER', 'admin_dashboard')
    return redirect(next_url)


def test_firebase(request):
    db.collection("test").add({
        "message": "Hello from Django"
    })

    return HttpResponse("Data sent to Firebase")

IMGBB_API_KEY = "f4d21e33dfe671434b7306e2a1abd8e5"

def upload_image(request):
    if request.method == "POST":
        image = request.FILES.get('image')
        if image:
            image_base64 = base64.b64encode(image.read()).decode('utf-8')

            url = "https://api.imgbb.com/1/upload"

            payload = {
                "key": IMGBB_API_KEY,
                "image": image_base64
            }

            response = requests.post(url, data=payload)

            if response.status_code == 200:
                image_url = response.json()['data']['url']

                db.collection("images").add({
                    "image_url": image_url
                })

                return render(request, "main/upload.html", {"url": image_url})

    return render(request, "main/upload.html")

def show_images(request):
    docs = db.collection("images").stream()

    images = []

    for doc in docs:
        images.append(doc.to_dict())

    return render(request, "main/show.html", {"images": images})

