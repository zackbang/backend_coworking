#!/usr/bin/env python3
"""
Script untuk menambahkan data sample ke database
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, UserRole, Workspace, Facility, Booking, BookingStatus
from app.auth import hash_password
from datetime import datetime, timedelta

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def seed_data():
    db = get_db()
    
    try:
        # Clear existing data
        db.query(Booking).delete()
        db.query(Workspace).delete()
        db.query(Facility).delete()
        db.query(User).delete()
        db.commit()
        
        # Create facilities
        facilities = [
            Facility(name="WiFi"),
            Facility(name="Air Conditioning"),
            Facility(name="Printer"),
            Facility(name="Coffee Machine"),
            Facility(name="Meeting Room"),
            Facility(name="Parking"),
            Facility(name="Security"),
            Facility(name="Receptionist"),
        ]
        
        for facility in facilities:
            db.add(facility)
        db.commit()
        
        # Create admin user
        admin_user = User(
            name="Admin",
            email="admin@coworking.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create sample customer
        customer_user = User(
            name="John Doe",
            email="john@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer_user)
        db.commit()
        db.refresh(customer_user)
        
        # Get facilities for workspace
        wifi = db.query(Facility).filter(Facility.name == "WiFi").first()
        ac = db.query(Facility).filter(Facility.name == "Air Conditioning").first()
        printer = db.query(Facility).filter(Facility.name == "Printer").first()
        coffee = db.query(Facility).filter(Facility.name == "Coffee Machine").first()
        meeting = db.query(Facility).filter(Facility.name == "Meeting Room").first()
        parking = db.query(Facility).filter(Facility.name == "Parking").first()
        
        # Create sample workspaces
        workspaces = [
            Workspace(
                admin_id=admin_user.id,
                name="Creative Hub Jakarta",
                address="Jl. Sudirman No. 123, Jakarta Selatan",
                description="Modern coworking space dengan view kota Jakarta. Cocok untuk startup dan freelancer yang membutuhkan inspirasi.",
                price_per_hour=50000,
                capacity=20,
                facilities=[wifi, ac, printer, coffee, parking]
            ),
            Workspace(
                admin_id=admin_user.id,
                name="Tech Space Bandung",
                address="Jl. Dago Raya No. 456, Bandung",
                description="Coworking space khusus untuk tech startup dengan fasilitas meeting room dan high-speed internet.",
                price_per_hour=45000,
                capacity=15,
                facilities=[wifi, ac, printer, meeting, parking]
            ),
            Workspace(
                admin_id=admin_user.id,
                name="Business Center Surabaya",
                address="Jl. Tunjungan No. 789, Surabaya",
                description="Professional coworking space di pusat bisnis Surabaya. Dilengkapi dengan fasilitas meeting room dan receptionist.",
                price_per_hour=60000,
                capacity=25,
                facilities=[wifi, ac, printer, coffee, meeting, parking]
            ),
            Workspace(
                admin_id=admin_user.id,
                name="Innovation Lab Yogyakarta",
                address="Jl. Malioboro No. 321, Yogyakarta",
                description="Coworking space dengan suasana kreatif dan inspiratif. Cocok untuk designer dan creative worker.",
                price_per_hour=40000,
                capacity=12,
                facilities=[wifi, ac, printer, coffee]
            ),
            Workspace(
                admin_id=admin_user.id,
                name="Startup Hub Medan",
                address="Jl. Imam Bonjol No. 654, Medan",
                description="Coworking space yang mendukung ekosistem startup di Medan. Dengan fasilitas lengkap dan komunitas yang aktif.",
                price_per_hour=35000,
                capacity=18,
                facilities=[wifi, ac, printer, coffee, meeting, parking]
            ),
        ]
        
        for workspace in workspaces:
            db.add(workspace)
        db.commit()
        
        print("✅ Data sample berhasil ditambahkan!")
        print(f"📊 Admin user: admin@coworking.com / admin123")
        print(f"👤 Sample customer: john@example.com / password123")
        print(f"🏢 {len(workspaces)} workspace telah ditambahkan")
        print(f"🔧 {len(facilities)} fasilitas telah ditambahkan")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
