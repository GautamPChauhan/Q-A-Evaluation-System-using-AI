-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3307
-- Generation Time: Sep 24, 2025 at 04:58 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `edusystem_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `admin_id` int(11) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `contact` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`admin_id`, `full_name`, `contact`) VALUES
(1, 'Chauhan Gautam', '9685749685');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `description`) VALUES
(2, '5 Year Int. Msc Computer Science', 'Bsc + Msc for CS');

-- --------------------------------------------------------

--
-- Table structure for table `evaluations`
--

CREATE TABLE `evaluations` (
  `evaluation_id` int(11) NOT NULL,
  `answer_id` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `feedback` text DEFAULT NULL,
  `evaluated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `exams`
--

CREATE TABLE `exams` (
  `exam_id` int(11) NOT NULL,
  `exam_name` varchar(100) NOT NULL,
  `teacher_id` int(5) NOT NULL,
  `course_id` int(11) NOT NULL,
  `semester_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `topic` varchar(255) NOT NULL,
  `question_excel_path` varchar(255) DEFAULT NULL,
  `max_marks` int(11) NOT NULL,
  `min_marks` int(11) NOT NULL,
  `exam_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `exams`
--

INSERT INTO `exams` (`exam_id`, `exam_name`, `teacher_id`, `course_id`, `semester_id`, `subject_id`, `topic`, `question_excel_path`, `max_marks`, `min_marks`, `exam_date`, `start_time`, `end_time`) VALUES
(3, 'Basics of Python Exam', 23, 2, 1, 1, 'Basics of Python', 'static/uploads\\python_questions.xlsx', 55, 16, '2025-09-30', '10:30:00', '12:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `questions`
--

CREATE TABLE `questions` (
  `question_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `semester_id` int(11) NOT NULL,
  `exam_id` int(5) NOT NULL,
  `subject_id` int(5) NOT NULL,
  `question_text` text NOT NULL,
  `model_answer` text NOT NULL,
  `max_score` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `questions`
--

INSERT INTO `questions` (`question_id`, `course_id`, `semester_id`, `exam_id`, `subject_id`, `question_text`, `model_answer`, `max_score`) VALUES
(1, 2, 1, 3, 1, 'What is Python?', 'Python is a high-level, interpreted, object-oriented programming language known for its simplicity and readability.', 2),
(2, 2, 1, 3, 1, 'Differentiate between list and tuple in Python.', 'List: Mutable, defined with []. Tuple: Immutable, defined with ().', 3),
(3, 2, 1, 3, 1, 'Explain the concept of Python functions with an example.', 'A function is a block of reusable code. Example:\n```python\ndef add(a,b): return a+b\nprint(add(2,3))```', 5),
(4, 2, 1, 3, 1, 'What are Python decorators?', 'Decorators are functions that modify the behavior of other functions without changing their code. Example: @staticmethod.', 5),
(5, 2, 1, 3, 1, 'Explain exception handling in Python.', 'Exception handling is done using try, except, finally. Example:\n```python\ntry:\n x=1/0\nexcept ZeroDivisionError:\n print(\'Error!\')```', 5),
(6, 2, 1, 3, 1, 'What is Pandas in Python?', 'Pandas is a library for data analysis and manipulation providing DataFrame and Series objects.', 3),
(7, 2, 1, 3, 1, 'What is NumPy in Python?', 'NumPy is a library for numerical computing in Python. It provides N-dimensional array objects and mathematical functions.', 3),
(8, 2, 1, 3, 1, 'Explain the difference between shallow copy and deep copy.', 'Shallow Copy: Copies object references, changes affect original. Deep Copy: Creates new copy of objects, changes do not affect original.', 4),
(9, 2, 1, 3, 1, 'What are Python modules and packages?', 'Module: A single Python file. Package: A collection of modules in a directory with __init__.py.', 3),
(10, 2, 1, 3, 1, 'Explain the use of \'with\' statement in Python.', 'The \'with\' statement is used to simplify resource management (like file handling). Example:\n```python\nwith open(\'file.txt\',\'r\') as f:\n data=f.read()```', 4),
(11, 2, 1, 3, 1, 'What is the difference between is and == operator in Python?', 'is: checks identity (same memory). ==: checks equality of values.', 3),
(12, 2, 1, 3, 1, 'Explain Python\'s garbage collection mechanism.', 'Python uses automatic garbage collection with reference counting and a cyclic garbage collector.', 4),
(13, 2, 1, 3, 1, 'What is a generator in Python?', 'Generators are special functions that return an iterator using \'yield\'. They allow lazy evaluation.', 4),
(14, 2, 1, 3, 1, 'Explain global and local variables with example.', 'Local variables: declared inside a function, accessible only there. Global variables: declared outside, accessible everywhere.\n```python\nx=10\ndef f():\n global x\n x=20```', 4),
(15, 2, 1, 3, 1, 'What are Python lambda functions?', 'Lambda functions are anonymous one-line functions. Example: `f = lambda x: x+2; print(f(3))`.', 3);

-- --------------------------------------------------------

--
-- Table structure for table `semesters`
--

CREATE TABLE `semesters` (
  `semester_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `semester_name` varchar(50) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `semesters`
--

INSERT INTO `semesters` (`semester_id`, `course_id`, `semester_name`, `start_date`, `end_date`) VALUES
(1, 2, 'Semester 1', '2025-09-24', '2026-01-25'),
(2, 2, 'Semester 2', '2025-09-24', '2026-01-16');

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `student_id` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `roll_no` int(5) DEFAULT NULL,
  `enrollment_no` bigint(15) DEFAULT NULL,
  `contact` varchar(20) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `course_id` int(11) DEFAULT NULL,
  `semester_id` int(11) DEFAULT NULL,
  `gender` varchar(6) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `university` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`student_id`, `full_name`, `roll_no`, `enrollment_no`, `contact`, `dob`, `course_id`, `semester_id`, `gender`, `address`, `department`, `university`) VALUES
(43, 'Not Provided', 1, 202528900101, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(44, 'Not Provided', 2, 202528900102, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(45, 'Not Provided', 3, 202528900103, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(46, 'Not Provided', 4, 202528900104, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(47, 'Not Provided', 5, 202528900105, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(48, 'Not Provided', 6, 202528900106, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided'),
(49, 'Not Provided', 7, 202528900107, 'Not Provided', NULL, 2, 1, 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided');

-- --------------------------------------------------------

--
-- Table structure for table `student_answers`
--

CREATE TABLE `student_answers` (
  `answer_id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `question_id` int(11) NOT NULL,
  `answer_text` text NOT NULL,
  `submitted_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `subjects`
--

CREATE TABLE `subjects` (
  `subject_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `semester_id` int(11) NOT NULL,
  `subject_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `subjects`
--

INSERT INTO `subjects` (`subject_id`, `course_id`, `semester_id`, `subject_name`) VALUES
(1, 2, 1, 'Python');

-- --------------------------------------------------------

--
-- Table structure for table `teachers`
--

CREATE TABLE `teachers` (
  `teacher_id` int(11) NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `last_degree` varchar(100) DEFAULT NULL,
  `contact` varchar(20) DEFAULT NULL,
  `gender` varchar(6) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `expertise` varchar(255) DEFAULT NULL,
  `subjects_taught` text DEFAULT NULL,
  `experience_years` int(11) DEFAULT NULL,
  `industry_experience_years` int(11) DEFAULT NULL,
  `research_papers` int(11) DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `university` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `teachers`
--

INSERT INTO `teachers` (`teacher_id`, `full_name`, `dob`, `last_degree`, `contact`, `gender`, `address`, `expertise`, `subjects_taught`, `experience_years`, `industry_experience_years`, `research_papers`, `department`, `university`) VALUES
(23, 'Nirmal', '2000-02-14', 'Phd Computer Science', '7990590144', 'Male', 'Sahvas app , Jivraj park', 'Web app', 'html , css , javascript', 2, 4, 2, 'Department of Computer Science', 'Gujarat University'),
(24, 'Not Provided', NULL, 'Not Provided', 'Not Provided', 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided', 0, 0, 0, 'Not Provided', 'Not Provided'),
(25, 'Not Provided', NULL, 'Not Provided', 'Not Provided', 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided', 0, 0, 0, 'Not Provided', 'Not Provided'),
(26, 'Not Provided', NULL, 'Not Provided', 'Not Provided', 'Not Pr', 'Not Provided', 'Not Provided', 'Not Provided', 0, 0, 0, 'Not Provided', 'Not Provided');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `uid` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `password_status` tinyint(4) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `modified_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `role` varchar(8) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`uid`, `email`, `password`, `password_status`, `created_at`, `modified_at`, `role`) VALUES
(1, 'gautam@gmail.com', 'admin123', 0, '2025-09-23 15:32:03', '2025-09-23 15:32:03', 'admin'),
(23, 'nirmal140204@gmail.com', 'scrypt:32768:8:1$OWYr4bmHpuBeyVsE$5ab9cce296518ae7303f1845aa7937800989cc6c4732874b2acb5fae7156686c48cc3281f20a4508274a7a6ad2d82ed5643bb2649c5d22f657613b0bf42d20c7', 0, '2025-09-23 20:24:29', '2025-09-23 20:24:29', 'teacher'),
(24, 'amanmistri45@gmail.com', 'scrypt:32768:8:1$Cz6i7Q9w6l5OKb7n$943d21ec36921f7fa6d0ce2c7bca2dd5b0b49364f581371530b76d6b76e498af0736694fef96a8f54e17105aa581ede92a65aea0e6007ef1044d88f2f8943c64', 0, '2025-09-23 20:24:35', '2025-09-23 20:24:35', 'teacher'),
(25, 'chauhangautam176@Gmail.com', 'scrypt:32768:8:1$zzoOQ8rnHdPGcDXH$72ceb29a35cb8f093950f81f67e306753b979926bf4dd1417c3946c5f3c7e0c35d200de7eb11e02510edc3d8731a91e5825eb1df06eb71f0bb9f61a067d7886b', 0, '2025-09-23 20:24:40', '2025-09-23 20:24:40', 'teacher'),
(26, 'vanodiyaaman25@gmail.com', 'scrypt:32768:8:1$qvJNfKu0cTTyEkKe$46b752522e86534e6848aa438ada102461fb507f55cfe6e36541fad4139a461172e9b7714c13448aab2bb3083a28655f139dbf66fb9430fd2718ebaa4301d81e', 0, '2025-09-23 20:24:44', '2025-09-23 20:24:44', 'teacher'),
(43, 'aagamj2004@gmail.com', 'scrypt:32768:8:1$plBEmgvumm0tFJfk$8f7cf1694a4023b2d25acca9a9d98861e74d6185b5ee67e2a4694c1a378cbf4ed37c3c6b1c316db5a6269a99e166c1707203d327371fa92bf0893f948fe6e0f8', 0, '2025-09-24 20:07:27', '2025-09-24 20:07:27', 'student'),
(44, 'krish1404patel@gmail.com', 'scrypt:32768:8:1$BwQIFrOOSeLRnZeh$4374b35c650004903e9c3eeffdd9297362862eb64ead965f1de65b98cd4b4048d4de75340c1615ce18d93551dcbabb2d2f3b5f2d5fda1b79d30e3496402534be', 0, '2025-09-24 20:07:27', '2025-09-24 20:07:27', 'student'),
(45, 'keyurimakwana7@gmail.com', 'scrypt:32768:8:1$DcCAeJX0vtXKhtFh$435420d814af644d0658397a3040bfe02bfb7fb8177fc0640d734abb8186e11cb3b22f34e329b919cc95e0e29404d51e8423fa21ae70d20b8f9e360d5faf5775', 0, '2025-09-24 20:07:27', '2025-09-24 20:07:27', 'student'),
(46, 'chaudharihiren2004@gmail.com', 'scrypt:32768:8:1$P91FLIkiewZ6yM7s$15a1142fe65b149c49c3dbe40d68cbd05bcabf6287f6c519ee7beead751eb55a2ab2090e5028c338a24eb5ae807ebf32e58b8ef3d6cdf44549e872bb7c4769a3', 0, '2025-09-24 20:07:27', '2025-09-24 20:07:27', 'student'),
(47, 'netrajigneshpatel@gmail.com', 'scrypt:32768:8:1$sUQlUubRjBgyhJM0$0910f8081b625ca9c8539af399aed475c5e6f617f3cae6d69fc8928003f2e38740778ce7b053f045b281687a52c42d6e34c73b09a3886b11cd4479d95ac3b5f1', 0, '2025-09-24 20:07:28', '2025-09-24 20:07:28', 'student'),
(48, 'darshan24204@gmail.com', 'scrypt:32768:8:1$H5yVqu73zuRqPKKf$e544f98ee613fd96cadd8094710975818d4b404147a1329d40caf46c2082080f2488a556892c6edfd43af5397fd2364cf4c14ec1d5cf48aec752125dc689b331', 0, '2025-09-24 20:07:28', '2025-09-24 20:07:28', 'student'),
(49, 'prajapatijay2250@gmail.com', 'scrypt:32768:8:1$Wzj0fvzi0xe4ncDD$5cba1f1e51b49c51af03652ab30075f854fe4b1a7433fd04e2e810ee607a8775f5cf6a958bea0a610ebbde94f8c9ff5c998a75a06ea6db2046b6c3a101c33948', 0, '2025-09-24 20:07:28', '2025-09-24 20:07:28', 'student');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`admin_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`);

--
-- Indexes for table `evaluations`
--
ALTER TABLE `evaluations`
  ADD PRIMARY KEY (`evaluation_id`),
  ADD KEY `answer_id` (`answer_id`);

--
-- Indexes for table `exams`
--
ALTER TABLE `exams`
  ADD PRIMARY KEY (`exam_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `semester_id` (`semester_id`),
  ADD KEY `subject_id` (`subject_id`),
  ADD KEY `teacher_idfk` (`teacher_id`);

--
-- Indexes for table `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`question_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `semester_id` (`semester_id`),
  ADD KEY `exam_idfk` (`exam_id`),
  ADD KEY `subject_id` (`subject_id`);

--
-- Indexes for table `semesters`
--
ALTER TABLE `semesters`
  ADD PRIMARY KEY (`semester_id`),
  ADD KEY `course_id` (`course_id`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`student_id`),
  ADD UNIQUE KEY `enrollment_no` (`enrollment_no`),
  ADD UNIQUE KEY `unique_roll_no_per_course` (`roll_no`,`course_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `semester_id` (`semester_id`);

--
-- Indexes for table `student_answers`
--
ALTER TABLE `student_answers`
  ADD PRIMARY KEY (`answer_id`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `question_id` (`question_id`);

--
-- Indexes for table `subjects`
--
ALTER TABLE `subjects`
  ADD PRIMARY KEY (`subject_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `semester_id` (`semester_id`);

--
-- Indexes for table `teachers`
--
ALTER TABLE `teachers`
  ADD PRIMARY KEY (`teacher_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`uid`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `evaluations`
--
ALTER TABLE `evaluations`
  MODIFY `evaluation_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `exams`
--
ALTER TABLE `exams`
  MODIFY `exam_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `question_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `semesters`
--
ALTER TABLE `semesters`
  MODIFY `semester_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `student_answers`
--
ALTER TABLE `student_answers`
  MODIFY `answer_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `subjects`
--
ALTER TABLE `subjects`
  MODIFY `subject_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `uid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admins`
--
ALTER TABLE `admins`
  ADD CONSTRAINT `admins_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `users` (`uid`);

--
-- Constraints for table `evaluations`
--
ALTER TABLE `evaluations`
  ADD CONSTRAINT `evaluations_ibfk_1` FOREIGN KEY (`answer_id`) REFERENCES `student_answers` (`answer_id`);

--
-- Constraints for table `exams`
--
ALTER TABLE `exams`
  ADD CONSTRAINT `exams_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  ADD CONSTRAINT `exams_ibfk_2` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`semester_id`),
  ADD CONSTRAINT `exams_ibfk_3` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`),
  ADD CONSTRAINT `teacher_idfk` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`);

--
-- Constraints for table `questions`
--
ALTER TABLE `questions`
  ADD CONSTRAINT `exam_idfk` FOREIGN KEY (`exam_id`) REFERENCES `exams` (`exam_id`),
  ADD CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  ADD CONSTRAINT `questions_ibfk_2` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`semester_id`),
  ADD CONSTRAINT `subject_id` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`);

--
-- Constraints for table `semesters`
--
ALTER TABLE `semesters`
  ADD CONSTRAINT `semesters_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`);

--
-- Constraints for table `students`
--
ALTER TABLE `students`
  ADD CONSTRAINT `students_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`uid`),
  ADD CONSTRAINT `students_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  ADD CONSTRAINT `students_ibfk_3` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`semester_id`);

--
-- Constraints for table `student_answers`
--
ALTER TABLE `student_answers`
  ADD CONSTRAINT `student_answers_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`uid`),
  ADD CONSTRAINT `student_answers_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`);

--
-- Constraints for table `subjects`
--
ALTER TABLE `subjects`
  ADD CONSTRAINT `subjects_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  ADD CONSTRAINT `subjects_ibfk_2` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`semester_id`);

--
-- Constraints for table `teachers`
--
ALTER TABLE `teachers`
  ADD CONSTRAINT `teachers_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`uid`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
