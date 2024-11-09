import React, { useState, useRef } from 'react';
import emailjs from '@emailjs/browser';

const FormularioDenuncia = () => {
  const form = useRef(); // Referencia al formulario

  const [formData, setFormData] = useState({
    titulo: '',
    descripcion: '',
    entidad: '',
    fecha: '',
    implicados: '',
    archivo: null,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleFileChange = (e) => {
    setFormData({
      ...formData,
      archivo: e.target.files[0],
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Usando sendForm con la referencia al formulario
    emailjs.sendForm('service_jcj1xrj', 'template_26c7mje', form.current, '8lNy3RRLsrfv9tTJT')
      .then((result) => {
        console.log("Correo enviado: ", result.text);
        alert('Formulario enviado correctamente');
      })
      .catch((error) => {
        console.error("Error al enviar el correo: ", error.text);
        alert('Error al enviar el formulario');
      });
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="max-w-md w-full bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Formulario de Denuncia</h2>
        <form ref={form} onSubmit={handleSubmit} className="space-y-4" encType="multipart/form-data">
          <div>
            <label className="block font-semibold text-gray-700">Título de la denuncia</label>
            <input
              type="text"
              name="titulo"
              value={formData.titulo}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block font-semibold text-gray-700">Descripción del problema</label>
            <textarea
              name="descripcion"
              value={formData.descripcion}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            ></textarea>
          </div>

          <div>
            <label className="block font-semibold text-gray-700">Entidad Involucrada</label>
            <input
              type="text"
              name="entidad"
              value={formData.entidad}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-gray-700">Fecha del suceso</label>
            <input
              type="date"
              name="fecha"
              value={formData.fecha}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block font-semibold text-gray-700">Posibles implicados</label>
            <input
              type="text"
              name="implicados"
              value={formData.implicados}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-gray-700">Subir documento de respaldo</label>
            <input
              type="file"
              name="archivo" // Este nombre debe coincidir con el parámetro de EmailJS
              onChange={handleFileChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-500 text-white font-semibold py-2 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
};

export default FormularioDenuncia;
