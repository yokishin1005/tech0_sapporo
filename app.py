import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import base64
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Sequence, Numeric, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload

# Streamlitページの設定
st.set_page_config(page_title="ビールログ - 店舗マップ", layout="wide")

# カスタムCSS（変更なし）
st.markdown("""
<style>
    .stApp {
        background-color: #FFF8E1;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #3E2723;
        font-family: 'Meiryo', sans-serif;
    }
    .brand-card {
        border: 2px solid #FFCC80;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        background-color: white;
        transition: transform 0.2s;
    }
    .brand-card:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .mascot {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 100px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)

# データモデル定義
Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(String(255), primary_key=True)
    user_name = Column(String(50), nullable=False)
    user_mail = Column(String(255), nullable=False)
    user_password = Column(String(255), nullable=False)
    user_picture = Column(LargeBinary)
    user_profile = Column(Text)
    age = Column(Integer)
    gender = Column(String(50))
    posts = relationship('Post', back_populates='users')

class Post(Base):
    __tablename__ = 'posts'
    post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.user_id'))
    store_id = Column(Integer, ForeignKey('stores.store_id'))
    review = Column(Text)
    rating = Column(Integer)
    users = relationship('Users', back_populates='posts')
    photos = relationship('Photo', back_populates='post')
    store = relationship('Store', back_populates='posts')

class Photo(Base):
    __tablename__ = 'photos'
    photo_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'))
    photo_data = Column(LargeBinary)
    post = relationship('Post', back_populates='photos')

class Store(Base):
    __tablename__ = 'stores'
    store_id = Column(Integer, Sequence('store_id_seq'), primary_key=True, autoincrement=True)
    store_name = Column(String(255), nullable=False)
    store_address = Column(String(255), nullable=False)
    store_contact = Column(String(255), nullable=True)
    lat = Column(Numeric(10, 8))
    lng = Column(Numeric(11, 8))
    brand_id = Column(String(255), ForeignKey('brands.brand_id'))
    posts = relationship('Post', back_populates='store')
    brand = relationship('Brand', back_populates='stores')

class Brand(Base):
    __tablename__ = 'brands'
    brand_id = Column(Integer, Sequence('brand_id_seq'), primary_key=True, autoincrement=True)
    brand_name = Column(String(255), nullable=False)
    brand_picture = Column(LargeBinary)
    manufacturer_id = Column(String(255), ForeignKey('manufacturers.manufacturer_id'))
    manufacturer = relationship('Manufacturer', back_populates='brands')
    stores = relationship('Store', back_populates='brand')

class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    manufacturer_id = Column(Integer, Sequence('manufacturer_id_seq'), primary_key=True, autoincrement=True)
    manufacturer_name = Column(String(255), nullable=False)
    brands = relationship('Brand', back_populates='manufacturer')

# バックエンド処理
engine = create_engine('sqlite:///beerlog.db')
Session = sessionmaker(bind=engine)

def データベースから店舗取得():
    """
    データベースから店舗情報とそれに関連するブランド情報を取得する
    """
    session = Session()
    try:
        # joinedloadを使用して、関連するブランド情報も同時に取得
        stores = session.query(Store).options(joinedload(Store.brand)).all()
        # セッション内でデータを取得し、必要な情報をリストに格納
        stores_data = []
        for store in stores:
            store_data = {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'store_address': store.store_address,
                'store_contact': store.store_contact,
                'lat': store.lat,
                'lng': store.lng,
                'brand_id': store.brand_id,
                'brand_name': store.brand.brand_name if store.brand else '不明',
                'brand_picture': base64.b64encode(store.brand.brand_picture).decode('utf-8') if store.brand and store.brand.brand_picture else ''
            }
            stores_data.append(store_data)
        return stores_data
    finally:
        session.close()

def データベースからブランド取得():
    """
    データベースから全てのブランド情報を取得する
    """
    session = Session()
    try:
        brands = session.query(Brand).all()
        brands_data = []
        for brand in brands:
            brand_data = {
                'brand_id': brand.brand_id,
                'brand_name': brand.brand_name,
                'brand_picture': base64.b64encode(brand.brand_picture).decode('utf-8') if brand.brand_picture else ''
            }
            brands_data.append(brand_data)
        return brands_data
    finally:
        session.close()

# フロントエンド処理
def ビールアイコン作成(色):
    """
    指定された色のビールアイコンSVGを生成する関数
    """
    return f'''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="40" height="40">
        <defs>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
                <feOffset dx="0" dy="0" result="offsetblur"/>
                <feFlood flood-color="#000000" flood-opacity="0.5"/>
                <feComposite in2="offsetblur" operator="in"/>
                <feMerge>
                    <feMergeNode/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <linearGradient id="foam" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:white;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#f0f0f0;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="48" fill="white" stroke="#333" stroke-width="2"/>
        <g transform="translate(15,15) scale(0.7)" filter="url(#shadow)">
            <path d="M20,30 L80,30 L70,90 L30,90 Z" fill="{色}" stroke="#444" stroke-width="4">
                <animate attributeName="d" dur="5s" repeatCount="indefinite"
                    values="M20,30 L80,30 L70,90 L30,90 Z;
                            M22,30 L78,30 L68,90 L32,90 Z;
                            M20,30 L80,30 L70,90 L30,90 Z" />
            </path>
            <path d="M30,25 Q50,5 70,25" fill="url(#foam)" stroke="#ddd" stroke-width="4">
                <animate attributeName="d" dur="3s" repeatCount="indefinite"
                    values="M30,25 Q50,5 70,25;
                            M30,23 Q50,3 70,23;
                            M30,25 Q50,5 70,25" />
            </path>
            <circle cx="40" cy="50" r="5" fill="white" opacity="0.8">
                <animate attributeName="cy" dur="2s" repeatCount="indefinite"
                    values="50;45;50" />
            </circle>
            <circle cx="60" cy="60" r="4" fill="white" opacity="0.6">
                <animate attributeName="cy" dur="2.5s" repeatCount="indefinite"
                    values="60;55;60" />
            </circle>
        </g>
    </svg>
    '''

def カスタムアイコン作成(色):
    """
    Folium用のカスタムアイコンを作成する関数
    """
    beer_icon = ビールアイコン作成(色)
    encoded_icon = base64.b64encode(beer_icon.encode('utf-8')).decode('utf-8')
    return folium.CustomIcon(
        icon_image=f"data:image/svg+xml;base64,{encoded_icon}",
        icon_size=(40, 40)
    )

def マップ表示():
    """
    店舗マップを表示する関数
    """
    stores = データベースから店舗取得()
    brands = データベースからブランド取得()

    st.write("## 🍺 取り扱いブランド")
    brand_cols = st.columns(3)
    for i, brand in enumerate(brands):
        with brand_cols[i % 3]:
            st.markdown(f'''
                <div class="brand-card">
                    <img src="data:image/png;base64,{brand['brand_picture']}" style="max-width:100px;max-height:100px;">
                    <p><strong>{brand['brand_name']}</strong></p>
                </div>
            ''', unsafe_allow_html=True)

    m = folium.Map(location=[35.68, 139.70], zoom_start=12, control_scale=True)
    marker_cluster = MarkerCluster().add_to(m)

    brand_colors = {brand['brand_id']: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FF9A3C', '#A1C181'][i % 5] for i, brand in enumerate(brands)}

    for store in stores:
        icon = カスタムアイコン作成(brand_colors.get(store['brand_id'], '#CCCCCC'))
        
        tooltip = folium.Tooltip(f'''
            <div style="width:150px;text-align:center;">
                <h4>{store['store_name']}</h4>
                <img src="data:image/png;base64,{store['brand_picture']}" style="max-width:100px;max-height:100px;">
                <p><strong>{store['brand_name']}</strong></p>
            </div>
        ''')

        popup = folium.Popup(f'''
            <div style="width:200px">
                <h3>{store['store_name']}</h3>
                <p><strong>ブランド:</strong> {store['brand_name']}</p>
                <p><strong>住所:</strong> {store['store_address']}</p>
                <p><strong>連絡先:</strong> {store['store_contact']}</p>
            </div>
        ''', max_width=300)

        folium.Marker(
            location=[float(store['lat']), float(store['lng'])],
            icon=icon,
            popup=popup,
            tooltip=tooltip
        ).add_to(marker_cluster)

    legend_html = '''
         <div style="position: fixed; 
         bottom: 50px; right: 50px; width: 220px;
         border:2px solid grey; z-index:9999; font-size:14px;
         background-color:rgba(255, 255, 255, 0.8); border-radius: 5px; padding: 10px;
         ">
         <p><strong>ブランド凡例</strong></p>
         '''
    for brand in brands:
        legend_html += f'<p><svg width="20" height="20" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="{brand_colors.get(brand["brand_id"], '#CCCCCC')}"/></svg> {brand["brand_name"]}</p>'
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))

    st.write("## 🗺️ 店舗マップ")
    folium_static(m, width=1000, height=600)

def main():
    """
    メイン関数：アプリケーションのエントリーポイント
    """
    st.title("🍺 びあろぐ")
    st.subheader("お気に入りのビールブランドと店舗を見つけよう！")

    st.markdown("""
    <div class="mascot">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+CiAgPGNpcmNsZSBjeD0iNTAiIGN5PSI1MCIgcj0iNDUiIGZpbGw9IiNGRkQ3MDAiLz4KICA8Y2lyY2xlIGN4PSIzNSIgY3k9IjQwIiByPSI1IiBmaWxsPSIjMDAwIi8+CiAgPGNpcmNsZSBjeD0iNjUiIGN5PSI0MCIgcj0iNSIgZmlsbD0iIzAwMCIvPgogIDxwYXRoIGQ9Ik0zNSA3MEg2NSIgc3Ryb2tlPSIjMDAwIiBzdHJva2Utd2lkdGg9IjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgogIDxwYXRoIGQ9Ik0yMCA2MFE1MCA4MCA4MCA2MCIgc3Ryb2tlPSIjQjg4NjBCIiBzdHJva2Utd2lkdGg9IjQiIGZpbGw9Im5vbmUiLz4KPC9zdmc+" alt="ビールログ マスコット">
    </div>
    """, unsafe_allow_html=True)

    マップ表示()

if __name__ == "__main__":
    main()