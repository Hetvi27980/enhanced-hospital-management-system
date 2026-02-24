import time


#   PATIENT & PRIORITY QUEUE


class Patient:
    def __init__(self, patient_id, name, age, gender, severity, arrival_time, disease=None):
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.gender = gender
        self.severity = severity
        self.arrival_time = arrival_time
        self.disease = disease
        self.history = []
        self.treatments = []
        self.room_id = None

    def __lt__(self, other):
        # Lower severity -> higher priority
        if self.severity != other.severity:
            return self.severity < other.severity
        # If same severity, older patient first
        elif self.age != other.age:
            return self.age < other.age
        # If same age, earlier arrival first
        else:
            return self.arrival_time < other.arrival_time

    def add_history(self, record):
        self.history.append(record)

    def add_treatment(self, treatment):
        self.treatments.append(treatment)


class MinHeapPriorityQueue:
    def __init__(self):
        self.heap = []

    def add_patient(self, patient):
        self.heap.append(patient)
        self._up_heap(len(self.heap) - 1)

    def _up_heap(self, index):
        while index > 0:
            parent_index = (index - 1) // 2
            if self.heap[index] < self.heap[parent_index]:
                self.heap[index], self.heap[parent_index] = self.heap[parent_index], self.heap[index]
                index = parent_index
            else:
                break

    def rebuild_heap(self):
        """Rebuild the heap from scratch to ensure proper heap property."""
        # Heapify from the last parent node up to root
        n = len(self.heap)
        if n <= 1:
            return
        # Start from the last parent node (n // 2 - 1) and go up
        for i in range(n // 2 - 1, -1, -1):
            self._down_heap(i)

    def get_next_patient(self):
        if not self.heap:
            return None
        return self.heap[0]

    def _down_heap(self, index):
        while True:
            left_child = 2 * index + 1
            right_child = 2 * index + 2
            smallest = index

            if left_child < len(self.heap) and self.heap[left_child] < self.heap[smallest]:
                smallest = left_child
            if right_child < len(self.heap) and self.heap[right_child] < self.heap[smallest]:
                smallest = right_child

            if smallest != index:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
            else:
                break

    def remove_patient(self, patient_id):
        for index, patient in enumerate(self.heap):
            if patient.patient_id == patient_id:
                last_patient = self.heap.pop()
                if index < len(self.heap):
                    self.heap[index] = last_patient
                    if index > 0 and self.heap[index] < self.heap[(index - 1) // 2]:
                        self._up_heap(index)
                    else:
                        self._down_heap(index)
                return True
        return False

    def display_patients(self):
        if not self.heap:
            print("No patients in priority queue")
            return
        print("\nPatients in Priority Queue (ordered by priority):")
        print("-" * 50)
        for patient in sorted(self.heap):
            print(f"ID: {patient.patient_id}")
            print(f"Name: {patient.name}")
            print(f"Age: {patient.age}")
            print(f"Gender: {patient.gender}")
            print(f"Severity: {patient.severity}")
            print(f"Room: {patient.room_id}")
            print(f"Disease: {patient.disease}")
            print("-" * 30)



#   ROOMS & HOSPITAL GRAPH


class Room:
    def __init__(self, room_id, is_vacant=True, room_type="General"):
        self.room_id = room_id
        self.is_vacant = is_vacant
        self.room_type = room_type
        self.condition = "Clean"

    def __str__(self):
        return f"{self.room_id} - {self.room_type} (Vacant: {self.is_vacant}, Condition: {self.condition})"



#   TREATMENTS & DLL

class Treatment:
    def __init__(self, treatment_id, patient_id, staff_id, treatment_details, date):
        self.treatment_id = treatment_id
        self.patient_id = patient_id
        self.staff_id = staff_id
        self.treatment_details = treatment_details
        self.date = date


class DLLNode:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, data):
        new_node = DLLNode(data)
        if not self.head:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node

    def traverse_forward(self):
        current = self.head
        while current:
            print(current.data)
            current = current.next

    def traverse_backward(self):
        current = self.tail
        while current:
            print(current.data)
            current = current.prev

    def list_data(self):
        current = self.head
        data_list = []
        while current:
            data_list.append(current.data)
            current = current.next
        return data_list



#   AVL TREE FOR PATIENTS


class AVLNode:
    def __init__(self, patient):
        self.patient = patient
        self.left = None
        self.right = None
        self.height = 1


class AVLTree:
    def __init__(self):
        self.root = None

    def height(self, node):
        if not node:
            return 0
        return node.height

    def balance_factor(self, node):
        if not node:
            return 0
        return self.height(node.left) - self.height(node.right)

    def right_rotate(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = max(self.height(y.left), self.height(y.right)) + 1
        x.height = max(self.height(x.left), self.height(x.right)) + 1
        return x

    def left_rotate(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = max(self.height(x.left), self.height(x.right)) + 1
        y.height = max(self.height(y.left), self.height(y.right)) + 1
        return y

    def insert(self, patient):
        if not self.root:
            self.root = AVLNode(patient)
            return
        self.root = self._insert_recursive(self.root, patient)

    def _insert_recursive(self, node, patient):
        if not node:
            return AVLNode(patient)

        if patient.patient_id < node.patient.patient_id:
            node.left = self._insert_recursive(node.left, patient)
        else:
            node.right = self._insert_recursive(node.right, patient)

        node.height = max(self.height(node.left), self.height(node.right)) + 1
        balance = self.balance_factor(node)

        # LL
        if balance > 1 and patient.patient_id < node.left.patient.patient_id:
            return self.right_rotate(node)
        # RR
        if balance < -1 and patient.patient_id > node.right.patient.patient_id:
            return self.left_rotate(node)
        # LR
        if balance > 1 and patient.patient_id > node.left.patient.patient_id:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)
        # RL
        if balance < -1 and patient.patient_id < node.right.patient.patient_id:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)

        return node

    def find_patient(self, patient_id):
        return self._find_recursive(self.root, patient_id)

    def _find_recursive(self, node, patient_id):
        if not node:
            return None
        if patient_id == node.patient.patient_id:
            return node.patient
        elif patient_id < node.patient.patient_id:
            return self._find_recursive(node.left, patient_id)
        else:
            return self._find_recursive(node.right, patient_id)

    def delete_patient(self, patient_id):
        self.root = self._delete_recursive(self.root, patient_id)

    def _delete_recursive(self, node, patient_id):
        if not node:
            return None

        if patient_id < node.patient.patient_id:
            node.left = self._delete_recursive(node.left, patient_id)
        elif patient_id > node.patient.patient_id:
            node.right = self._delete_recursive(node.right, patient_id)
        else:
            # node to delete
            if not node.left:
                return node.right
            elif not node.right:
                return node.left

            temp = self._min_value_node(node.right)
            node.patient = temp.patient
            node.right = self._delete_recursive(node.right, temp.patient.patient_id)

        if not node:
            return None

        node.height = max(self.height(node.left), self.height(node.right)) + 1
        balance = self.balance_factor(node)

        # LL
        if balance > 1 and self.balance_factor(node.left) >= 0:
            return self.right_rotate(node)
        # LR
        if balance > 1 and self.balance_factor(node.left) < 0:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)
        # RR
        if balance < -1 and self.balance_factor(node.right) <= 0:
            return self.left_rotate(node)
        # RL
        if balance < -1 and self.balance_factor(node.right) > 0:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)

        return node

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def display_patients(self):
        self._display_preorder(self.root)

    def _display_preorder(self, node):
        if node:
            patient = node.patient
            print(f"\nID: {patient.patient_id}")
            print(f"Name: {patient.name}")
            print(f"Age: {patient.age}")
            print(f"Gender: {patient.gender}")
            print(f"Severity: {patient.severity}")
            print(f"Room: {patient.room_id}")
            if patient.disease:
                print(f"Disease: {patient.disease}")
            print("-" * 30)
            self._display_preorder(node.left)
            self._display_preorder(node.right)



#   ROOMS, STAFF


class Staff:
    def __init__(self, staff_id, name, role):
        self.staff_id = staff_id
        self.name = name
        self.role = role

    def __str__(self):
        return f"{self.name} ({self.role}) - ID: {self.staff_id}"


class StaffManager:
    def __init__(self):
        self.staff = []

    def add_staff(self, staff):
        self.staff.append(staff)

    def list_staff(self):
        return self.staff


class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.initialize_rooms()

    def initialize_rooms(self):
        self.rooms["Reception"] = Room("Reception", is_vacant=False)
        self.rooms["Room 1"] = Room("Room 1", room_type="General")
        self.rooms["Room 2"] = Room("Room 2", room_type="ICU")
        self.rooms["Room 3"] = Room("Room 3", room_type="Surgery")
        self.rooms["Room 4"] = Room("Room 4", room_type="General")
        self.rooms["Power and Monitoring Hub"] = Room("Power and Monitoring Hub", is_vacant=False)

    def find_nearest_vacant_room(self, start_room_id):
        # Simple implementation: find first vacant room (excluding Reception and Hub)
        for room_id, room in self.rooms.items():
            if room.is_vacant and room_id not in ["Reception", "Power and Monitoring Hub"]:
                return room_id
        return None

    def get_vacant_rooms(self):
        return [room_id for room_id, room in self.rooms.items() if room.is_vacant]

    def list_rooms(self):
        return [str(room) for room in self.rooms.values()]



#   MAIN HOSPITAL SYSTEM


class EnhancedHospitalSystem:
    def __init__(self):
        self.avl_tree = AVLTree()
        self.room_manager = RoomManager()
        self.staff_manager = StaffManager()
        self.treatment_log = DoublyLinkedList()
        self.priority_queue = MinHeapPriorityQueue()
        self.current_id = 0

    # ---- New method: backend-friendly patient insert (for GUI usage) ----
    def add_patient_record(self, name, age, gender, severity, disease=None):
        """
        Add a patient without using input(), so Tkinter or other
        frontends can call this. Returns (success: bool, message: str).
        """
        try:
            if not 1 <= severity <= 3:
                return False, "Severity must be between 1 and 3"

            self.current_id += 1
            arrival_time = time.time()

            nearest_room = self.room_manager.find_nearest_vacant_room("Reception")
            if not nearest_room:
                return False, "No vacant rooms available for admission."

            patient = Patient(self.current_id, name, age, gender, severity, arrival_time, disease)
            patient.room_id = nearest_room
            patient.add_history(f"Patient admitted at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            self.avl_tree.insert(patient)
            self.priority_queue.add_patient(patient)
            self.room_manager.rooms[nearest_room].is_vacant = False

            return True, f"Patient added successfully with ID: {self.current_id} (Room: {nearest_room})"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def display_detailed_patient_info(self, patient):
        print("\n" + "=" * 50)
        print("DETAILED PATIENT INFORMATION")
        print("=" * 50)

        print("\n📋 BASIC INFORMATION:")
        print("-" * 30)
        print(f"Patient ID: {patient.patient_id}")
        print(f"Name: {patient.name}")
        print(f"Age: {patient.age}")
        print(f"Gender: {patient.gender}")
        print(f"Severity Level: {patient.severity}")

        print("\n📍 LOCATION INFORMATION:")
        print("-" * 30)
        if patient.room_id:
            room = self.room_manager.rooms.get(patient.room_id)
            if room:
                print(f"Room Number: {patient.room_id}")
                print(f"Room Type: {room.room_type}")
                print(f"Room Condition: {room.condition}")
        else:
            print("Room: Not assigned")

        print("\n🏥 MEDICAL INFORMATION:")
        print("-" * 30)
        if patient.disease:
            print(f"Current Diagnosis: {patient.disease}")
        else:
            print("Current Diagnosis: Not recorded")

        print("\n💉 TREATMENT INFORMATION:")
        print("-" * 30)
        if patient.treatments:
            for i, treatment in enumerate(patient.treatments, 1):
                print(f"Treatment #{i}: {treatment}")

            treatment_records = []
            current = self.treatment_log.head
            while current:
                if current.data.patient_id == patient.patient_id:
                    treatment_records.append(current.data)
                current = current.next

            if treatment_records:
                print("\nDetailed Treatment Records:")
                for record in treatment_records:
                    print(f"\nTreatment ID: {record.treatment_id}")

                    staff_member = None
                    for staff in self.staff_manager.staff:
                        if staff.staff_id == record.staff_id:
                            staff_member = staff
                            break

                    if staff_member:
                        print(f"Performed by: {staff_member.name} ({staff_member.role})")
                    print(f"Date: {record.date}")
                    print(f"Details: {record.treatment_details}")
        else:
            print("No treatments recorded")

        print("\n📜 MEDICAL HISTORY:")
        print("-" * 30)
        if patient.history:
            for i, record in enumerate(patient.history, 1):
                print(f"{i}. {record}")
        else:
            print("No medical history recorded")

        print("\n" + "=" * 50)

    def find_patient_details(self):
        try:
            patient_id = int(input("Enter Patient ID: "))
            patient = self.avl_tree.find_patient(patient_id)
            if patient:
                self.display_detailed_patient_info(patient)
            else:
                print("Patient not found")
        except ValueError:
            print("Please enter valid input")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def list_patients(self):
        print("\n=== Current Patients (AVL Tree Order) ===")
        if not self.avl_tree.root:
            print("No patients currently in the system.")
        else:
            self.avl_tree.display_patients()

        print("\n=== Current Patients (Priority Queue Order) ===")
        self.priority_queue.display_patients()

    def get_next_priority_patient(self):
        next_patient = self.priority_queue.get_next_patient()
        if next_patient:
            print("\nNext priority patient for treatment:")
            print(f"ID: {next_patient.patient_id}")
            print(f"Name: {next_patient.name}")
            print(f"Age: {next_patient.age}")
            print(f"Gender: {next_patient.gender}")
            print(f"Severity: {next_patient.severity}")
            if next_patient.room_id:
                print(f"Room: {next_patient.room_id}")
            if next_patient.disease:
                print(f"Disease: {next_patient.disease}")
        else:
            print("No patients in priority queue")

    def list_staff(self):
        print("\n=== Hospital Staff ===")
        staff_list = self.staff_manager.list_staff()
        if not staff_list:
            print("No staff members registered in the system.")
            return
        for staff in staff_list:
            print(f"ID: {staff.staff_id}")
            print(f"Name: {staff.name}")
            print(f"Role: {staff.role}")
            print("-" * 30)

    def add_staff(self):
        try:
            staff_id = input("Enter Staff ID: ")
            name = input("Enter Staff Name: ")
            role = input("Enter Staff Role: ")

            if not all([staff_id, name, role]):
                raise ValueError("All fields must be filled")

            new_staff = Staff(staff_id, name, role)
            self.staff_manager.add_staff(new_staff)
            print(f"\nStaff member {name} added successfully with ID: {staff_id}")

        except ValueError as e:
            print(f"Error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

    def add_patient(self):
        try:
            name = input("Enter patient name: ")
            age = int(input("Enter patient age: "))
            gender = input("Enter patient gender: ")
            severity = int(input("Enter severity (1: Critical, 2: Moderate, 3: Mild): "))
            if not 1 <= severity <= 3:
                raise ValueError("Severity must be between 1 and 3")
            disease = input("Enter disease (optional): ").strip() or None

            self.current_id += 1
            arrival_time = time.time()

            nearest_room = self.room_manager.find_nearest_vacant_room("Reception")
            if not nearest_room:
                print("No vacant rooms available for admission.")
                return

            patient = Patient(self.current_id, name, age, gender, severity, arrival_time, disease)
            patient.room_id = nearest_room
            patient.add_history(f"Patient admitted at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            self.avl_tree.insert(patient)
            self.priority_queue.add_patient(patient)
            self.room_manager.rooms[nearest_room].is_vacant = False

            print(f"\nPatient added successfully with ID: {self.current_id}")
            print(f"Assigned to room: {nearest_room}")

        except ValueError as e:
            print(f"Error: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def discharge_patient(self):
        try:
            patient_id = int(input("Enter patient ID to discharge: "))
            patient = self.avl_tree.find_patient(patient_id)

            if patient:
                if patient.room_id:
                    self.room_manager.rooms[patient.room_id].is_vacant = True
                self.avl_tree.delete_patient(patient_id)
                self.priority_queue.remove_patient(patient_id)
                print(f"Patient {patient.name} discharged successfully from room {patient.room_id}")
            else:
                print("Patient not found")

        except ValueError:
            print("Please enter a valid patient ID")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def add_treatment(self):
        try:
            treatment_id = input("Enter Treatment ID: ")
            patient_id = int(input("Enter Patient ID: "))

            patient = self.avl_tree.find_patient(patient_id)
            if not patient:
                print("Patient not found.")
                return

            staff_id = input("Enter Staff ID: ")
            staff_exists = False
            for staff in self.staff_manager.staff:
                if staff.staff_id == staff_id:
                    staff_exists = True
                    break
            if not staff_exists:
                print("Staff member not found.")
                return

            treatment_details = input("Enter Treatment Details: ")
            date = time.strftime("%Y-%m-%d")

            new_treatment = Treatment(treatment_id, patient_id, staff_id, treatment_details, date)
            self.treatment_log.append(new_treatment)

            patient.add_history(
                f"Treatment '{treatment_details}' performed on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            patient.add_treatment(treatment_details)

            print(f"\nTreatment {treatment_id} recorded successfully for patient {patient.name}")

        except ValueError as e:
            print(f"Error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

    def show_treatment_records(self):
        print("\n=== Treatment Records ===")
        treatments = self.treatment_log.list_data()
        if not treatments:
            print("No treatment records found.")
            return

        for treatment in treatments:
            print(f"\nTreatment ID: {treatment.treatment_id}")
            print(f"Patient ID: {treatment.patient_id}")
            patient = self.avl_tree.find_patient(treatment.patient_id)
            if patient:
                print(f"Patient Name: {patient.name}")
            print(f"Staff ID: {treatment.staff_id}")
            print(f"Treatment Details: {treatment.treatment_details}")
            print(f"Date: {treatment.date}")
            print("-" * 30)

    def run(self):
        while True:
            print("\n=== Enhanced Hospital Management System ===")
            print("1. Add Patient")
            print("2. Discharge Patient")
            print("3. List Patients")
            print("4. List Staff")
            print("5. Add Staff")
            print("6. Add Treatment")
            print("7. Show Treatment Records")
            print("8. Get Next Priority Patient")
            print("9. Find Patient")
            print("10. Exit")
            print("=========================================")

            try:
                choice = input("Enter your choice (1-10): ")

                if choice == '1':
                    self.add_patient()
                elif choice == '2':
                    self.discharge_patient()
                elif choice == '3':
                    self.list_patients()
                elif choice == '4':
                    self.list_staff()
                elif choice == '5':
                    self.add_staff()
                elif choice == '6':
                    self.add_treatment()
                elif choice == '7':
                    self.show_treatment_records()
                elif choice == '8':
                    self.get_next_priority_patient()
                elif choice == '9':
                    self.find_patient_details()
                elif choice == '10':
                    print("Thank you for using the Enhanced Hospital Management System.")
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 10.")

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                print("Please try again.")



#   MAIN ENTRY POINT


if __name__ == "__main__":
    hospital_system = EnhancedHospitalSystem()
    hospital_system.run()
